#!/usr/bin/env python3
"""
compare_policies.py  -  SFT vs GRPO policy comparison (the Stage-4 result check).

Samples N completions per design from TWO adapters (the SFT policy and the GRPO
policy), oracle-gates each, and records the surrogate Fmax of the correct ones
PLUS keeps the distinct-correct RTL (with sample multiplicity) for real Vivado
synthesis. Two questions:

  1. did GRPO shift the policy toward FAST designs?  -> compare per-design
     correct-rate and mean/max surrogate Fmax (server-only, instant);
  2. is that shift REAL or surrogate-gaming?  -> the emitted .sv (tagged by
     policy, with multiplicity) go to run_ppa; compare frequency-weighted REAL
     Fmax sft vs grpo. If real Fmax rises like the surrogate says, it's real;
     if the surrogate inflated (e.g. firr8 566 MHz) but Vivado doesn't, it gamed.

    python compare_policies.py --sft sft_v4_out --grpo grpo_v6 \
        --surrogate surrogate.pt --n 24 --out-dir rtl/policy_cmp
Then (laptop): run_ppa --dir rtl/policy_cmp ... ; then compare_eval.py.
"""

import os
import re
import json
import argparse
from collections import defaultdict

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
from probe_competence import probe_prompts, generate
from surrogate_train import extract_features

DEFAULT_DESIGNS = ["fir8_8b", "fir16_8b", "fir32_8b", "firr8", "firr16",
                   "poly4_8b", "poly6_8b", "poly8_v3_8b"]


def load_surrogate(path, device):
    ck = torch.load(path, map_location=device, weights_only=False)
    n = len(ck["feat_names"])
    net = nn.Sequential(nn.Linear(n, 32), nn.ReLU(), nn.Linear(32, 32),
                        nn.ReLU(), nn.Linear(32, 1))
    net.load_state_dict(ck["state"]); net.eval().to(device)
    mu = torch.tensor(ck["mu"], dtype=torch.float32, device=device)
    sd = torch.tensor(ck["sd"], dtype=torch.float32, device=device)

    @torch.no_grad()
    def pred(rtl):
        x = torch.tensor(extract_features(rtl), dtype=torch.float32, device=device)
        return float(np.exp(net(((x - mu) / sd).unsqueeze(0)).item()))
    return pred


def norm(rtl):
    body = re.sub(r"\bmodule\s+\w+", "module M", rtl, count=1)
    return re.sub(r"\s+", " ", body).strip()


def eval_policy(tag, adapter, base, tok, prompts, predict, args, dev, mani):
    model = PeftModel.from_pretrained(base, adapter, is_trainable=False).eval()
    print(f"\n=== {tag} ({adapter}) ===", flush=True)
    print(f"{'design':12s} {'corr%':>6s} {'meanF':>7s} {'maxF':>6s}")
    rows = {}
    for d, (_, prompt) in prompts.items():
        texts = generate(model, tok, prompt, args.n, args.temp, args.max_tokens,
                         batch=args.gen_batch)
        fm = []
        distinct = {}      # norm(rtl) -> [count, rtl_text]
        for t in texts:
            rtl = extract_verilog(t, d)
            if rtl is None:
                continue
            rtl = rtl.encode("ascii", "replace").decode("ascii")
            try:
                ok = oracle.score(rtl, d)["correct"]
            except Exception:
                ok = False
            if not ok:
                continue
            fm.append(predict(rtl))
            key = norm(rtl)
            if key in distinct:
                distinct[key][0] += 1
            else:
                distinct[key] = [1, rtl]
        corr = 100.0 * len(fm) / args.n
        mF = float(np.mean(fm)) if fm else 0.0
        xF = float(max(fm)) if fm else 0.0
        rows[d] = {"corr_pct": corr, "mean_surr_fmax": mF, "max_surr_fmax": xF,
                   "n_correct": len(fm), "n": args.n}
        print(f"{d:12s} {corr:6.1f} {mF:7.1f} {xF:6.1f}", flush=True)
        # write distinct-correct for Vivado, tagged with sample multiplicity
        for j, (cnt, rtl_text) in enumerate(distinct.values()):
            mod = f"{tag}__{d}__g{j}"
            rr = re.sub(r"\bmodule\s+" + re.escape(d) + r"\b",
                        "module " + mod, rtl_text, count=1)
            open(os.path.join(args.out_dir, mod + ".sv"), "w").write(rr)
            mani[mod] = {"policy": tag, "design": d, "count": cnt, "n": args.n}
    del model
    torch.cuda.empty_cache()
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=os.environ.get(
        "RTLCODER_PATH", "/zeng_gk/Amine/mas/rtlcoder"))
    ap.add_argument("--sft", default="sft_v4_out")
    ap.add_argument("--grpo", default="grpo_v6")
    ap.add_argument("--surrogate", default="surrogate.pt")
    ap.add_argument("--designs", nargs="*", default=DEFAULT_DESIGNS)
    ap.add_argument("--n", type=int, default=24)
    ap.add_argument("--temp", type=float, default=1.0)
    ap.add_argument("--max-tokens", type=int, default=768)
    ap.add_argument("--gen-batch", type=int, default=8)
    ap.add_argument("--out-dir", default="rtl/policy_cmp")
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    prompts = probe_prompts(set(args.designs))
    tok = AutoTokenizer.from_pretrained(args.base)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    base = AutoModelForCausalLM.from_pretrained(
        args.base, torch_dtype=torch.float16, device_map={"": 0})
    dev = next(base.parameters()).device
    predict = load_surrogate(args.surrogate, dev)

    mani, summary = {}, {}
    summary["sft"] = eval_policy("sft", args.sft, base, tok, prompts, predict,
                                 args, dev, mani)
    summary["grpo"] = eval_policy("grpo", args.grpo, base, tok, prompts, predict,
                                  args, dev, mani)
    json.dump(mani, open(os.path.join(args.out_dir, "fmax_manifest.json"), "w"),
              indent=1)
    json.dump(summary, open(os.path.join(args.out_dir, "surrogate_summary.json"),
                            "w"), indent=1)

    print("\n=== SFT -> GRPO (surrogate Fmax; REAL Fmax comes from run_ppa) ===")
    print(f"{'design':12s} {'corr% s->g':>12s} {'meanF s->g':>16s}")
    for d in sorted(prompts):
        s, g = summary["sft"][d], summary["grpo"][d]
        print(f"{d:12s} {s['corr_pct']:5.0f}->{g['corr_pct']:<5.0f} "
              f"{s['mean_surr_fmax']:7.0f}->{g['mean_surr_fmax']:<7.0f}")
    print(f"\nwrote candidates + manifest -> {args.out_dir}\n"
          f"next (laptop): run_ppa.py --dir {args.out_dir} --out {args.out_dir}/"
          f"ppa.jsonl --clk clk --period 5.0 --vivado ...  then compare_eval.py")


if __name__ == "__main__":
    main()
