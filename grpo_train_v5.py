#!/usr/bin/env python3
"""
grpo_train_v5.py  -  Correctness-gated Fmax GRPO on the accelerator catalog.

The fix for grpo_v4's failure. grpo_v4 rewarded PPA on a pool that was NOT
correctness-gated, so the policy learned lean-but-WRONG token patterns and lost
functional correctness (KL exploded; mod108_counter 0/8). Here every training
completion is a functionally-CORRECT generation (the rtl/accel_probe pool is
iverilog-gated vs golden.py at generation time, gen_accel_candidates.py). The
reward is Fmax among those correct candidates, group-normalised per design, with
KL to the base model. Because the policy is only ever reinforced toward correct
completions, it is pushed toward correct-AND-fast RTL, not wrong-but-lean.

This is OFFLINE GRPO on the precomputed correct-candidate pool (Vivado Fmax is
too slow for an online per-rollout reward; correctness was gated online by
iverilog when the pool was built). Per design the group is its correct
generations; the group-relative advantage pushes toward the high-Fmax ones.

Inputs (from the probe pipeline):
  --probe-dir  rtl/accel_probe                 <design>__g<k>.sv (correct gens)
  --ppa        rtl/accel_probe/ppa.jsonl        module -> fmax_mhz (Vivado OOC)
  --manifest   rtl/accel_probe/probe_manifest.json  module -> {design, family}

Reward (group-normalised; only ranking matters):
  r = timing_weight * fmax_mhz  -  area_weight * lut
Only designs with >= --min-count correct candidates AND non-zero Fmax spread
give a gradient; others are skipped (no signal).

Run from /zeng_gk/Amine/mas:
  python fpga/grpo_train_v5.py --steps 400 --kl_coef 0.1 --timing-weight 1.0
Eval after: gen_accel_candidates.py --adapter grpo_v5 ... then run_ppa +
analyze_accel_spread (correctness must NOT drop; Fmax of correct gens should rise).
"""

import os
import re
import json
import time
import random
import argparse
import collections

os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("HF_HUB_OFFLINE", "1")

import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import LoraConfig, get_peft_model, TaskType

import score_accel as SA
from build_dataset import make_prompt, LLM_DIR
from grpo_train_v3 import pick_dtype, upcast_trainable, seq_mean_logprob

HERE = os.path.dirname(os.path.abspath(__file__))


def load_pool(probe_dir, ppa_path, manifest_path, min_count):
    """design -> [{rtl (original module name), fmax, lut}] for every correct
    synthesized candidate; only designs with >= min_count kept."""
    mani = json.load(open(manifest_path))
    ppa = {}
    for line in open(ppa_path):
        try:
            p = json.loads(line)
        except ValueError:
            continue
        if p.get("compiled"):
            ppa[p["module"]] = p
    bydesign = collections.defaultdict(list)
    for mod, info in mani.items():
        if mod not in ppa:
            continue
        sv = os.path.join(probe_dir, mod + ".sv")
        if not os.path.exists(sv):
            continue
        design = info["design"]
        # un-rename <design>__g<k> back to the design name so the trained
        # completion matches the prompt interface (module <design> ( ... ))
        rtl = re.sub(r"\bmodule\s+" + re.escape(mod) + r"\b",
                     "module " + design, open(sv).read(), count=1)
        bydesign[design].append({"rtl": rtl,
                                 "fmax": ppa[mod].get("fmax_mhz", 0.0),
                                 "lut": ppa[mod].get("lut", 0)})
    return {d: c for d, c in bydesign.items() if len(c) >= min_count}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base_model",
                    default=os.environ.get("RTLCODER_PATH",
                                           os.path.join(LLM_DIR, "rtlcoder")))
    ap.add_argument("--out", default="grpo_v5")
    ap.add_argument("--probe-dir", default=os.path.join("fpga", "rtl", "accel_probe"))
    ap.add_argument("--ppa", default=os.path.join("fpga", "rtl", "accel_probe", "ppa.jsonl"))
    ap.add_argument("--manifest",
                    default=os.path.join("fpga", "rtl", "accel_probe", "probe_manifest.json"))
    ap.add_argument("--min-count", type=int, default=2)
    ap.add_argument("--steps", type=int, default=400)
    ap.add_argument("--timing-weight", type=float, default=1.0,
                    help="reward per MHz of Fmax")
    ap.add_argument("--area-weight", type=float, default=0.0,
                    help="penalty per LUT (default 0: optimise Fmax only)")
    ap.add_argument("--lr", type=float, default=1e-5)
    ap.add_argument("--kl_coef", type=float, default=0.1,
                    help="KL to base (>= v4's 0.05; v4 collapsed)")
    ap.add_argument("--max-tokens", type=int, default=512)
    ap.add_argument("--dtype", choices=["auto", "fp16", "bf16"], default="auto")
    ap.add_argument("--save_every", type=int, default=100)
    ap.add_argument("--log", default="grpo_v5_log.jsonl")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    random.seed(args.seed)
    torch.manual_seed(args.seed)
    os.makedirs(args.out, exist_ok=True)

    def rp(p):
        return p if os.path.isabs(p) else os.path.join(os.getcwd(), p)

    def reward(c):
        return args.timing_weight * c["fmax"] - args.area_weight * c["lut"]

    pool = load_pool(rp(args.probe_dir), rp(args.ppa), rp(args.manifest),
                     args.min_count)

    designs, weights, prompts = [], [], {}
    for d, cands in pool.items():
        spec_path = os.path.join(SA.RTL_LIB, d, "spec.txt")
        if not os.path.exists(spec_path):
            continue
        prompts[d] = make_prompt({"name": d}, open(spec_path).read())
        spread = float(np.std([reward(c) for c in cands]))
        if spread < 1e-6:        # all candidates same Fmax -> no gradient
            continue
        designs.append(d)
        weights.append(spread)
    if not designs:
        print("no designs with Fmax spread among correct candidates -- the base "
              "model does not expose headroom here (probe was WEAK); use best-of-N "
              "reranking instead of RL.")
        return
    print(f"correctness-gated pool: {len(designs)} designs with Fmax spread "
          f"(>={args.min_count} correct candidates each)", flush=True)
    for d in sorted(designs):
        fs = [c["fmax"] for c in pool[d]]
        print(f"  {d:10s} n={len(pool[d]):2d} fmax[{min(fs):.0f}-{max(fs):.0f}]",
              flush=True)

    dtype = pick_dtype(args.dtype)
    print(f"\nloading {args.base_model} ({dtype})...", flush=True)
    tok = AutoTokenizer.from_pretrained(args.base_model)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    base = AutoModelForCausalLM.from_pretrained(
        args.base_model, torch_dtype=dtype, device_map={"": 0})
    base.config.use_cache = True
    model = get_peft_model(base, LoraConfig(
        task_type=TaskType.CAUSAL_LM, r=16, lora_alpha=32, lora_dropout=0.0,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"], bias="none"))
    model.print_trainable_parameters()
    trainable = upcast_trainable(model, dtype)
    dev = next(model.parameters()).device
    opt = torch.optim.AdamW(trainable, lr=args.lr)
    scaler = torch.cuda.amp.GradScaler(enabled=(dtype == torch.float16))
    log = open(args.log, "a")

    print(f"\nGRPO-v5 (correctness-gated Fmax): {args.steps} steps, "
          f"timing_w={args.timing_weight}, area_w={args.area_weight}, "
          f"kl={args.kl_coef}\n", flush=True)

    for step in range(args.steps):
        t0 = time.time()
        d = random.choices(designs, weights=weights, k=1)[0]
        cands = pool[d]
        chat = tok.apply_chat_template(
            [{"role": "user", "content": prompts[d]}],
            tokenize=False, add_generation_prompt=True)
        prompt_ids = tok(chat, return_tensors="pt",
                         return_token_type_ids=False).input_ids.to(dev)
        r = torch.tensor([reward(c) for c in cands], dtype=torch.float32)
        if r.std() < 1e-6:
            continue
        adv = (r - r.mean()) / (r.std() + 1e-8)

        opt.zero_grad(set_to_none=True)
        loss_val = kl_val = 0.0
        for c, a in zip(cands, adv.tolist()):
            gid = tok(c["rtl"], return_tensors="pt",
                      return_token_type_ids=False).input_ids.to(dev)[0]
            gid = gid[:args.max_tokens]
            lp = seq_mean_logprob(model, prompt_ids, gid, use_adapter=True)
            base_lp = seq_mean_logprob(model, prompt_ids, gid,
                                       use_adapter=False).detach()
            dd = base_lp - lp
            kl = torch.exp(dd) - dd - 1.0
            loss = (-a * lp + args.kl_coef * kl) / len(cands)
            scaler.scale(loss).backward()
            loss_val += loss.item()
            kl_val += kl.item() / len(cands)
        scaler.unscale_(opt)
        torch.nn.utils.clip_grad_norm_(trainable, 1.0)
        scaler.step(opt)
        scaler.update()

        log.write(json.dumps({"step": step, "design": d, "n": len(cands),
                              "loss": loss_val, "kl": kl_val}) + "\n")
        log.flush()
        print(f"[{step:4d}] {d:10s} n={len(cands)} "
              f"fmax[{min(c['fmax'] for c in cands):.0f}-"
              f"{max(c['fmax'] for c in cands):.0f}] "
              f"loss={loss_val:.4f} kl={kl_val:.4f} {time.time()-t0:.0f}s",
              flush=True)
        if (step + 1) % args.save_every == 0:
            model.save_pretrained(os.path.join(args.out, f"step_{step + 1}"))
            print(f"  -> checkpoint: {args.out}/step_{step + 1}", flush=True)

    model.save_pretrained(args.out)
    tok.save_pretrained(args.out)
    log.close()
    print(f"\nGRPO-v5 done. Adapter -> {args.out}/\n"
          f"eval: python fpga/gen_accel_candidates.py --adapter {args.out} "
          f"--out-dir fpga/rtl/accel_eval_v5  (correctness must hold; then run_ppa "
          f"+ analyze_accel_spread to check the Fmax distribution shifted up)")


if __name__ == "__main__":
    main()
