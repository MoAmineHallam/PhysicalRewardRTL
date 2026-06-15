#!/usr/bin/env python3
"""
grpo_train_v4.py  -  Offline PPA-augmented GRPO (learned generation).

Teaches the model to GENERATE physically-efficient RTL (high Fmax / low area)
among functionally-correct designs -- the supervisor's RL-PPA direction.

Synthesis is too slow (~1-2 min/candidate) for an online per-rollout PPA
reward, so this trains OFFLINE on the precomputed correct-candidate PPA pool
(gen_ppa_set -> run_ppa). For each design the group is its functionally-correct
candidates; the reward is their PPA quality; the group-relative advantage
pushes the policy toward the lean/fast implementations and away from the
bloated ones (e.g. a correct 14-bit counter: 2 LUTs vs 18). KL to the base
model (adapter-disable) prevents collapse.

Inputs (from the PPA-spread pipeline, committed under fpga/rtl/ppa_set/):
  --ppa       rtl/ppa_set/ppa.jsonl              module -> fmax_mhz/lut/ff/...
  --manifest  rtl/ppa_set/ppa_set_manifest.json  module -> {design, family}
  --cand-dir  rtl/ppa_set/cand                   module.sv -> candidate RTL

Reward (group-normalised, so absolute scale is irrelevant -- only ranking):
  r = timing_weight * fmax_mhz  -  area_weight * lut
Designs with <2 synthesized correct candidates give no relative signal and are
skipped; designs are sampled proportional to their reward spread (the headroom).

Run from /zeng_gk/Amine/mas:
  python fpga/grpo_train_v4.py --steps 400 --area-weight 1.0 --timing-weight 0.05
"""

import os
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

import score_candidate as SC
from build_dataset import make_prompt, LLM_DIR
from gen_candidate_bitstream import rename_module
from grpo_train_v3 import pick_dtype, upcast_trainable, seq_mean_logprob

HERE = os.path.dirname(os.path.abspath(__file__))


def load_pool(ppa_path, manifest_path, cand_dir, min_count):
    """design -> [{rtl (original module name), fmax, lut, family}] for every
    synthesized correct candidate; only designs with >= min_count kept."""
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
        sv = os.path.join(cand_dir, mod + ".sv")
        if not os.path.exists(sv):
            continue
        # un-rename module back to the design name so the trained completion
        # matches the prompt interface (module <design> ( ... ))
        rtl = rename_module(open(sv).read(), mod, info["design"])
        bydesign[info["design"]].append({
            "rtl": rtl, "fmax": ppa[mod].get("fmax_mhz", 0.0),
            "lut": ppa[mod].get("lut", 0), "family": info["family"]})
    return {d: c for d, c in bydesign.items() if len(c) >= min_count}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base_model",
                    default=os.environ.get("RTLCODER_PATH",
                                           os.path.join(LLM_DIR, "rtlcoder")))
    ap.add_argument("--out", default="grpo_v4")
    ap.add_argument("--ppa", default=os.path.join("rtl", "ppa_set", "ppa.jsonl"))
    ap.add_argument("--manifest",
                    default=os.path.join("rtl", "ppa_set", "ppa_set_manifest.json"))
    ap.add_argument("--cand-dir", default=os.path.join("rtl", "ppa_set", "cand"))
    ap.add_argument("--min-count", type=int, default=2)
    ap.add_argument("--steps", type=int, default=400)
    ap.add_argument("--area-weight", type=float, default=1.0,
                    help="penalty per LUT (area minimisation)")
    ap.add_argument("--timing-weight", type=float, default=0.05,
                    help="reward per MHz of Fmax")
    ap.add_argument("--lr", type=float, default=1e-5)
    ap.add_argument("--kl_coef", type=float, default=0.05)
    ap.add_argument("--max-tokens", type=int, default=512)
    ap.add_argument("--dtype", choices=["auto", "fp16", "bf16"], default="auto")
    ap.add_argument("--save_every", type=int, default=100)
    ap.add_argument("--log", default="grpo_v4_log.jsonl")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    random.seed(args.seed)
    torch.manual_seed(args.seed)
    os.makedirs(args.out, exist_ok=True)

    def rp(p):
        return p if os.path.isabs(p) else os.path.join(HERE, p)

    def ppa_reward(c):
        return args.timing_weight * c["fmax"] - args.area_weight * c["lut"]

    pool = load_pool(rp(args.ppa), rp(args.manifest), rp(args.cand_dir),
                     args.min_count)
    manifest = SC.load_manifest()

    designs, weights, prompts = [], [], {}
    for d, cands in pool.items():
        if d not in manifest:
            continue
        spec_path = os.path.join(SC.RTL_LIB, d, "spec.txt")
        if not os.path.exists(spec_path):
            continue
        prompts[d] = make_prompt(manifest[d], open(spec_path).read())
        spread = float(np.std([ppa_reward(c) for c in cands]))
        if spread < 1e-6:        # no PPA variance -> no gradient signal
            continue
        designs.append(d)
        weights.append(spread)
    if not designs:
        print("no designs with PPA spread -- expand the ppa_set (more "
              "arithmetic/sequential families, more candidates per design).")
        return
    print(f"PPA pool: {len(designs)} designs with PPA spread "
          f"(>={args.min_count} correct synthesized candidates each)", flush=True)

    dtype = pick_dtype(args.dtype)
    print(f"loading {args.base_model} ({dtype})...", flush=True)
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

    print(f"\nGRPO-v4 (offline PPA): {args.steps} steps, area_w="
          f"{args.area_weight}, timing_w={args.timing_weight}, kl={args.kl_coef}\n",
          flush=True)

    for step in range(args.steps):
        t0 = time.time()
        d = random.choices(designs, weights=weights, k=1)[0]
        cands = pool[d]
        chat = tok.apply_chat_template(
            [{"role": "user", "content": prompts[d]}],
            tokenize=False, add_generation_prompt=True)
        prompt_ids = tok(chat, return_tensors="pt",
                         return_token_type_ids=False).input_ids.to(dev)
        r = torch.tensor([ppa_reward(c) for c in cands], dtype=torch.float32)
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

        best = min(cands, key=lambda c: c["lut"])
        log.write(json.dumps({"step": step, "design": d, "n": len(cands),
                              "loss": loss_val, "kl": kl_val}) + "\n")
        log.flush()
        print(f"[{step:4d}] {d:18s} n={len(cands)} "
              f"lut[{min(c['lut'] for c in cands)}-{max(c['lut'] for c in cands)}] "
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
    print(f"\nGRPO-v4 done. Adapter -> {args.out}/")


if __name__ == "__main__":
    main()
