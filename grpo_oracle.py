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
  base model (LoRA continues from the SFT adapter, so we start competent).

Because incorrect completions get 0 and correct ones get their (positive) Fmax,
one reward simultaneously (a) keeps correctness and (b) pushes toward the fast
tail. Designs whose sampled group is all-wrong or all-same-reward give no gradient
and are skipped.

Start from the SFT adapter; KL anchors to base (disable_adapter). Validate AFTER
on Vivado/silicon (the surrogate is periodically re-anchored to real synthesis).

    python grpo_oracle.py --sft sft_v4_out --surrogate surrogate.pt \
        --base /zeng_gk/Amine/mas/rtlcoder --steps 300 --group 8 --out grpo_v6
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
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

import oracle
from build_dataset import extract_verilog
from probe_competence import probe_prompts
from surrogate_train import extract_features, FEAT_NAMES
from grpo_train_v3 import pick_dtype, upcast_trainable, seq_mean_logprob

DEFAULT_DESIGNS = ["fir8_8b", "fir16_8b", "fir32_8b", "firr8", "firr16",
                   "poly4_8b", "poly6_8b", "poly8_v3_8b"]


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
        return float(np.exp(out) if log_target else out)
    return predict_fmax


def sample_group(model, tok, prompt, g, temp, max_tokens, dev, batch=4):
    """Sample g completions; return list of (gen_ids_tensor, text)."""
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
                                  pad_token_id=tok.eos_token_id)
        for s in seqs:
            gen = s[plen:]
            out.append((gen.detach().clone(),
                        tok.decode(gen, skip_special_tokens=True)))
        remaining -= k
        torch.cuda.empty_cache()
    return inp["input_ids"], out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=os.environ.get(
        "RTLCODER_PATH", "/zeng_gk/Amine/mas/rtlcoder"))
    ap.add_argument("--sft", default="sft_v4_out", help="SFT adapter to start from")
    ap.add_argument("--surrogate", default="surrogate.pt")
    ap.add_argument("--out", default="grpo_v6")
    ap.add_argument("--designs", nargs="*", default=DEFAULT_DESIGNS)
    ap.add_argument("--steps", type=int, default=300)
    ap.add_argument("--group", type=int, default=8, help="candidates per step")
    ap.add_argument("--gen-batch", type=int, default=4)
    ap.add_argument("--temp", type=float, default=1.0)
    ap.add_argument("--max-tokens", type=int, default=768)
    ap.add_argument("--lr", type=float, default=1e-5)
    ap.add_argument("--kl_coef", type=float, default=0.1)
    ap.add_argument("--incorrect-reward", type=float, default=0.0)
    ap.add_argument("--dtype", choices=["auto", "fp16", "bf16"], default="auto")
    ap.add_argument("--save_every", type=int, default=100)
    ap.add_argument("--log", default="grpo_v6_log.jsonl")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    random.seed(args.seed); torch.manual_seed(args.seed)
    os.makedirs(args.out, exist_ok=True)
    prompts = probe_prompts(set(args.designs))
    designs = sorted(prompts)
    print(f"GRPO designs ({len(designs)}): {', '.join(designs)}", flush=True)

    dtype = pick_dtype(args.dtype)
    tok = AutoTokenizer.from_pretrained(args.base)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    base = AutoModelForCausalLM.from_pretrained(
        args.base, torch_dtype=dtype, device_map={"": 0})
    # continue the SFT LoRA as the trainable policy; disable_adapter() = base = KL ref
    model = PeftModel.from_pretrained(base, args.sft, is_trainable=True)
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
            lp = seq_mean_logprob(model, prompt_ids, gen_ids, use_adapter=True)
            base_lp = seq_mean_logprob(model, prompt_ids, gen_ids,
                                       use_adapter=False).detach()
            dd = base_lp - lp
            kl = torch.exp(dd) - dd - 1.0
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
            model.save_pretrained(os.path.join(args.out, f"step_{step+1}"))
            print(f"  -> checkpoint {args.out}/step_{step+1}", flush=True)

    model.save_pretrained(args.out); tok.save_pretrained(args.out)
    log.close()
    print(f"\nGRPO-oracle done. Adapter -> {args.out}/\n"
          f"eval: gen_fmax_candidates.py --adapter {args.out} --out-dir "
          f"rtl/grpo_eval, then run_ppa + analyze_accel_spread -- correctness must "
          f"hold and the Fmax distribution should shift UP vs the SFT policy.")


if __name__ == "__main__":
    main()
