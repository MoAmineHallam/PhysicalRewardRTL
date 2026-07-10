#!/usr/bin/env python3
"""
grpo_oracle.py  -  Stage 4: ONLINE correctness-gated Fmax GRPO (V2).

Unlike grpo_train_v5 (offline: reweights a FIXED pool of precomputed candidates),
this samples FRESH completions from the policy each step, so the policy can invent
faster implementations rather than just up-weighting existing ones. Affordable
because the reward needs no Vivado per sample:

  per candidate:  oracle.score (iverilog, ~1-2s)  ->  correct? : not
                  correct   -> reward = surrogate Fmax (RTL-text MLP, instant)
                  incorrect -> reward = 0   (the correctness GATE)
  group-normalise the rewards per design -> advantage; GRPO update with KL to the
  FROZEN SFT policy (F3: load the SFT adapter as both a trainable 'default' and a
  frozen 'ref'; KL anchors to 'ref', so the leash pulls toward SFT competence,
  not the base model).

Because incorrect completions get 0 and correct ones get their (positive) Fmax,
one reward simultaneously (a) keeps correctness and (b) pushes toward the fast
tail. Designs whose sampled group is all-wrong or all-same-reward give no gradient
and are skipped.

Phase-B hardening applied here: F2 (surrogate Fmax clamped to [5,500] so it can't
be gamed to inf), F3 (frozen-SFT KL ref), F4 (max-tokens 1536 so fir32/firr32
transposed fit), F8 (stop+trim at endmodule so the gradient ignores post-module
junk), F10 (train on ALL train-split designs, not the 8 pilot prompts). The
train-split design list is gen_sft_corpus.designs(exclude_holdout=True), and a
hard guard refuses to run if any §5 held-out design leaks in.

Start from sft_v5; validate AFTER on Vivado/silicon (surrogate re-anchored to
real synthesis). Held-out eval is eval_holdout.py (NEVER trained on).

    python grpo_oracle.py --sft sft_v5_out --surrogate surrogate_v2.pt \
        --base /zeng_gk/Amine/mas/rtlcoder --steps 400 --group 8 --out grpo_v7
"""

import os
import re
import json
import time
import random
import argparse

os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "0")

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

import oracle
import gen_sft_corpus as GSC
from build_dataset import extract_verilog
from probe_competence import probe_prompts
from surrogate_train import (extract_features, FEAT_NAMES,
                             LOGF_MIN, LOGF_MAX, clamp_fmax)
from grpo_train_v3 import pick_dtype, upcast_trainable


def train_split_designs():
    """F10: GRPO trains on ALL train-split designs (dozens of prompts), not the
    8-design pilot list -- more prompts reduce per-prompt overfitting and cover
    the grid. The train split is exactly gen_sft_corpus.designs(exclude_holdout=
    True), so the frozen §5 held-out designs can NEVER leak into RL."""
    return [name for name, _, _, _ in GSC.designs(exclude_holdout=True)]


def load_surrogate(path, device):
    ck = torch.load(path, map_location=device)
    nfeat = len(ck["feat_names"])
    net = nn.Sequential(nn.Linear(nfeat, 32), nn.ReLU(),
                        nn.Linear(32, 32), nn.ReLU(), nn.Linear(32, 1))
    net.load_state_dict(ck["state"]); net.eval().to(device)
    mu = torch.tensor(ck["mu"], dtype=torch.float32, device=device)
    sd = torch.tensor(ck["sd"], dtype=torch.float32, device=device)
    log_target = ck.get("log_target", True)

    @torch.no_grad()
    def predict_fmax(rtl_text):
        x = torch.tensor(extract_features(rtl_text), dtype=torch.float32,
                         device=device)
        out = net(((x - mu) / sd).unsqueeze(0)).item()
        if log_target:
            # F2: clamp in LOG space BEFORE exp, so an out-of-range MLP head can
            # never overflow to +inf (the poly4 gaming mode). exp(clamped) is
            # then guaranteed in [5, 500]; clamp_fmax is a belt-and-braces cap.
            out = min(max(out, LOGF_MIN), LOGF_MAX)
            return clamp_fmax(float(np.exp(out)))
        return clamp_fmax(float(out))
    return predict_fmax


def seq_logprob_adapter(model, prompt_ids, gen_ids, adapter, grad):
    """Mean per-token log-prob of gen_ids under a NAMED PEFT adapter.

    F3: the KL reference must be the FROZEN SFT policy, not the base model. We
    load the SFT adapter twice -- 'default' (trainable policy) and 'ref' (frozen)
    -- and select which one is active per forward pass. grad=False (the reference
    path) wraps the forward in no_grad; the caller detaches. Length-normalised,
    fp32 softmax (matches grpo_train_v3.seq_mean_logprob, but adapter-selectable)."""
    model.set_adapter(adapter)
    full = torch.cat([prompt_ids[0], gen_ids]).unsqueeze(0)
    if grad:
        logits = model(full).logits
    else:
        with torch.no_grad():
            logits = model(full).logits
    plen = prompt_ids.shape[1]
    gl = logits[0, plen - 1: plen - 1 + gen_ids.shape[0], :]
    lp = F.log_softmax(gl.float(), dim=-1)
    return lp[torch.arange(gen_ids.shape[0], device=lp.device), gen_ids].mean()


def trim_endmodule(gen_ids, tok):
    """F8: cut gen_ids at the end of the FIRST 'endmodule' so the GRPO gradient
    (logprob over the whole sampled sequence) is not diluted by post-endmodule
    junk -- the reward is already computed on the extracted module only. Decode
    incrementally and keep the shortest token prefix whose text contains a
    complete 'endmodule'; fall back to the full (eos-trimmed) sequence."""
    # fast path: trim trailing eos/pad first
    nz = (gen_ids != tok.eos_token_id).nonzero()
    if nz.numel():
        gen_ids = gen_ids[: int(nz[-1].item()) + 1]
    full_txt = tok.decode(gen_ids, skip_special_tokens=True)
    pos = full_txt.find("endmodule")
    if pos < 0:
        return gen_ids, full_txt
    target = full_txt[: pos + len("endmodule")]
    # find the smallest prefix of tokens whose decode already covers `target`
    lo, hi = 1, gen_ids.shape[0]
    while lo < hi:
        mid = (lo + hi) // 2
        if "endmodule" in tok.decode(gen_ids[:mid], skip_special_tokens=True):
            hi = mid
        else:
            lo = mid + 1
    return gen_ids[:lo], target


def sample_group(model, tok, prompt, g, temp, max_tokens, dev, batch=4):
    """Sample g completions; return list of (gen_ids_tensor, text).

    Generation stops at 'endmodule' (stop_strings) so large designs are not
    truncated mid-module by the token cap AND no junk trails the module; each
    sequence is then trimmed to end exactly at its own 'endmodule' (F8)."""
    chat = tok.apply_chat_template([{"role": "user", "content": prompt}],
                                   tokenize=False, add_generation_prompt=True)
    inp = tok(chat, return_tensors="pt", return_token_type_ids=False).to(dev)
    plen = inp["input_ids"].shape[1]
    out = []
    remaining = g
    model.config.use_cache = True
    while remaining > 0:
        k = min(batch, remaining)
        with torch.inference_mode():
            seqs = model.generate(**inp, max_new_tokens=max_tokens,
                                  do_sample=True, temperature=temp,
                                  num_return_sequences=k,
                                  stop_strings=["endmodule"], tokenizer=tok,
                                  pad_token_id=tok.eos_token_id)
        for s in seqs:
            gen, text = trim_endmodule(s[plen:], tok)
            out.append((gen.detach().clone(), text))
        remaining -= k
        torch.cuda.empty_cache()
    return inp["input_ids"], out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=os.environ.get(
        "RTLCODER_PATH", "/zeng_gk/Amine/mas/rtlcoder"))
    ap.add_argument("--sft", default="sft_v5_out", help="SFT adapter to start from")
    ap.add_argument("--surrogate", default="surrogate_v2.pt")
    ap.add_argument("--out", default="grpo_v7")
    ap.add_argument("--designs", nargs="*", default=None,
                    help="default = ALL train-split designs (F10); pass names to override")
    ap.add_argument("--steps", type=int, default=400)
    ap.add_argument("--group", type=int, default=8, help="candidates per step")
    ap.add_argument("--gen-batch", type=int, default=4)
    ap.add_argument("--temp", type=float, default=1.0)
    ap.add_argument("--max-tokens", type=int, default=1536)   # F4: fit fir32/firr32 transposed
    ap.add_argument("--lr", type=float, default=1e-5)
    ap.add_argument("--kl_coef", type=float, default=0.1)
    ap.add_argument("--incorrect-reward", type=float, default=0.0)
    ap.add_argument("--dtype", choices=["auto", "fp16", "bf16"], default="auto")
    ap.add_argument("--save_every", type=int, default=100)
    ap.add_argument("--log", default="grpo_v7_log.jsonl")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    random.seed(args.seed); torch.manual_seed(args.seed)
    os.makedirs(args.out, exist_ok=True)
    want = set(args.designs) if args.designs else set(train_split_designs())
    prompts = probe_prompts(want)                 # F10: dozens of train prompts
    designs = sorted(prompts)
    # hard guard: the frozen §5 held-out designs must NEVER enter the GRPO list
    leaked = [d for d in designs if GSC.is_holdout(d)]
    if leaked:
        raise SystemExit(f"HELD-OUT LEAK into GRPO designs: {leaked} "
                         f"(§5 isolation violated -- refusing to train)")
    print(f"GRPO designs ({len(designs)}, train-split only): "
          f"{', '.join(designs)}", flush=True)

    dtype = pick_dtype(args.dtype)
    tok = AutoTokenizer.from_pretrained(args.base)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    base = AutoModelForCausalLM.from_pretrained(
        args.base, torch_dtype=dtype, device_map={"": 0})
    # F3: load the SFT LoRA TWICE -- 'default' (trainable, the RL policy) and
    # 'ref' (frozen, the KL anchor). Previously KL anchored to the BASE model
    # (disable_adapter), which mildly pulled the policy AWAY from SFT competence.
    # Both adapters are tiny (LoRA r=16 x 4 proj), so this adds no real memory.
    # The trainable adapter keeps the name 'default' so save_pretrained writes it
    # to args.out/ directly (the frozen 'ref' goes to a subdir we never reload),
    # keeping the downstream from_pretrained(base, grpo_v7) convention intact.
    model = PeftModel.from_pretrained(base, args.sft, is_trainable=True)
    model.load_adapter(args.sft, adapter_name="ref", is_trainable=False)
    model.set_adapter("default")                  # 'default' is the trainable policy
    model.print_trainable_parameters()
    trainable = upcast_trainable(model, dtype)
    dev = next(model.parameters()).device
    opt = torch.optim.AdamW(trainable, lr=args.lr)
    scaler = torch.cuda.amp.GradScaler(enabled=(dtype == torch.float16))
    predict_fmax = load_surrogate(args.surrogate, dev)
    log = open(args.log, "a")

    print(f"\nGRPO-oracle: {args.steps} steps, group={args.group}, "
          f"kl={args.kl_coef}, temp={args.temp}\n", flush=True)

    for step in range(args.steps):
        t0 = time.time()
        d = random.choice(designs)
        _, prompt = prompts[d]
        model.set_adapter("default")             # sample from the current policy
        prompt_ids, group = sample_group(model, tok, prompt, args.group,
                                         args.temp, args.max_tokens, dev,
                                         args.gen_batch)
        rewards, n_correct = [], 0
        for gen_ids, text in group:
            rtl = extract_verilog(text, d)
            r = args.incorrect_reward
            if rtl is not None:
                rtl = rtl.encode("ascii", "replace").decode("ascii")
                try:
                    ok = oracle.score(rtl, d)["correct"]
                except Exception:
                    ok = False
                if ok:
                    r = predict_fmax(rtl); n_correct += 1
            rewards.append(r)
        r = torch.tensor(rewards, dtype=torch.float32)
        if r.std() < 1e-6:                      # no gradient signal -> skip
            print(f"[{step:4d}] {d:10s} correct={n_correct}/{args.group} "
                  f"(flat reward, skip) {time.time()-t0:.0f}s", flush=True)
            continue
        adv = (r - r.mean()) / (r.std() + 1e-8)

        model.config.use_cache = False
        opt.zero_grad(set_to_none=True)
        loss_val = kl_val = 0.0
        for (gen_ids, _), a in zip(group, adv.tolist()):
            gen_ids = gen_ids[:args.max_tokens].to(dev)
            if gen_ids.numel() < 2:
                continue
            # F3: KL anchor is the FROZEN SFT policy ('ref'), not the base model.
            # ref path is no_grad + detached; policy path carries the gradient.
            ref_lp = seq_logprob_adapter(model, prompt_ids, gen_ids,
                                         "ref", grad=False).detach()
            lp = seq_logprob_adapter(model, prompt_ids, gen_ids,
                                     "default", grad=True)
            dd = ref_lp - lp
            kl = torch.exp(dd) - dd - 1.0         # k3 estimator, >= 0
            loss = (-a * lp + args.kl_coef * kl) / len(group)
            scaler.scale(loss).backward()
            loss_val += loss.item(); kl_val += kl.item() / len(group)
        scaler.unscale_(opt)
        torch.nn.utils.clip_grad_norm_(trainable, 1.0)
        scaler.step(opt); scaler.update()

        rec = {"step": step, "design": d, "correct": n_correct,
               "mean_fmax": float(np.mean([x for x in rewards if x > 0]) or 0),
               "max_fmax": float(max(rewards)), "loss": loss_val, "kl": kl_val}
        log.write(json.dumps(rec) + "\n"); log.flush()
        print(f"[{step:4d}] {d:10s} correct={n_correct}/{args.group} "
              f"surrFmax[max={rec['max_fmax']:.0f}] loss={loss_val:.4f} "
              f"kl={kl_val:.4f} {time.time()-t0:.0f}s", flush=True)
        if (step + 1) % args.save_every == 0:
            # save ONLY the trainable policy (default); 'ref' is a frozen copy of
            # the SFT adapter we never need to reload.
            model.save_pretrained(os.path.join(args.out, f"step_{step+1}"),
                                  selected_adapters=["default"])
            print(f"  -> checkpoint {args.out}/step_{step+1}", flush=True)

    model.save_pretrained(args.out, selected_adapters=["default"])
    tok.save_pretrained(args.out)
    log.close()
    print(f"\nGRPO-oracle done. Adapter -> {args.out}/\n"
          f"eval: gen_fmax_candidates.py --adapter {args.out} --out-dir "
          f"rtl/grpo_eval, then run_ppa + analyze_accel_spread -- correctness must "
          f"hold and the Fmax distribution should shift UP vs the SFT policy.")


if __name__ == "__main__":
    main()
