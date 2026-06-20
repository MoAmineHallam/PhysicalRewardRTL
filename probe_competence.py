#!/usr/bin/env python3
"""
probe_competence.py  -  V2 competence probe (the gate before GRPO).

Question this answers: did the SFT warm-start lift base correctness above the
RL foothold? RL refines competence, it cannot create it -- the cross-model probe
measured ~2% correct, which is no foothold. After sft_train_v2 we re-measure here
RIGOROUSLY:

  * prompts use the EXACT corpus format the model was trained on
    (gen_sft_corpus.make_prompt: NL spec + module interface), not the V1 prompt;
  * the verdict is the V2 ORACLE (I/O-equivalence under directed+random stimulus,
    latency-aligned), not the V1 counter-Hamming score;
  * base vs SFT are compared on the SAME model object by toggling the LoRA
    adapter (PeftModel.disable_adapter), so the only variable is the weights.

Per design it reports correct/N (oracle 'correct') and compile-rate, for base and
(if --adapter) SFT, plus family and overall correct-rate. That overall number is
the GRPO gate.

Runs on the GPU server:
    python probe_competence.py --adapter sft_v2_out --n 16
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

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

import gen_sft_corpus as GSC
import oracle
from build_dataset import extract_verilog

# Representative spread across families and sizes (override with --designs).
DEFAULT_DESIGNS = ["fir4_8b", "fir8_8b", "fir16_8b", "fir32_8b",
                   "firr8", "firr16", "poly3_8b", "poly6_8b",
                   "cordic8", "cordic12"]


def probe_prompts(want):
    """name -> (family, corpus-format prompt), built exactly like training."""
    out = {}
    for name, fam, spec, styles in GSC.designs():
        if name not in want:
            continue
        header_src = styles.get("ref") or next(iter(styles.values()))
        out[name] = (fam, GSC.make_prompt(spec, header_src))
    return out


def generate(model, tok, prompt, n, temp, max_tokens, batch=8):
    """Sample n completions, CHUNKED into sub-batches so only `batch` KV caches
    are live at once (n*max_tokens parallel KV caches OOM a 32GB V100)."""
    chat = (tok.apply_chat_template([{"role": "user", "content": prompt}],
                                    tokenize=False, add_generation_prompt=True)
            if tok.chat_template else prompt + "\n")
    inp = tok(chat, return_tensors="pt",
              return_token_type_ids=False).to(model.device)
    plen = inp["input_ids"].shape[1]
    texts, remaining = [], n
    while remaining > 0:
        k = min(batch, remaining)
        with torch.inference_mode():
            out = model.generate(**inp, max_new_tokens=max_tokens, do_sample=True,
                                 temperature=temp, num_return_sequences=k,
                                 pad_token_id=tok.eos_token_id)
        texts.extend(tok.decode(s[plen:], skip_special_tokens=True) for s in out)
        remaining -= k
        torch.cuda.empty_cache()
    return texts


def run_probe(label, model, tok, prompts, n, temp, max_tokens, n_stim):
    print(f"\n===== {label} =====", flush=True)
    fam_correct, fam_total = defaultdict(int), defaultdict(int)
    tot_correct = tot_compiled = tot = 0
    for name, (fam, prompt) in prompts.items():
        texts = generate(model, tok, prompt, n, temp, max_tokens)
        c = comp = 0
        for txt in texts:
            rtl = extract_verilog(txt, name)
            if rtl is None:
                continue
            rtl = rtl.encode("ascii", "replace").decode("ascii")
            try:
                r = oracle.score(rtl, name, n=n_stim)
            except Exception:
                continue
            comp += int(r["compiled"])
            c += int(r["correct"])
        fam_correct[fam] += c; fam_total[fam] += n
        tot_correct += c; tot_compiled += comp; tot += n
        print(f"  {name:10s} ({fam:6s})  correct {c:2d}/{n}   "
              f"compiled {comp:2d}/{n}", flush=True)
    print(f"  {'-'*44}")
    for fam in sorted(fam_total):
        print(f"  {fam:6s} correct-rate: "
              f"{fam_correct[fam]}/{fam_total[fam]} "
              f"= {100*fam_correct[fam]/fam_total[fam]:.1f}%")
    rate = 100 * tot_correct / tot if tot else 0.0
    print(f"  OVERALL correct-rate: {tot_correct}/{tot} = {rate:.1f}%  "
          f"(compiled {tot_compiled}/{tot})")
    return rate


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=os.environ.get(
        "RTLCODER_PATH", "/zeng_gk/Amine/mas/rtlcoder"))
    ap.add_argument("--adapter", default=None, help="LoRA dir (SFT output)")
    ap.add_argument("--designs", nargs="*", default=DEFAULT_DESIGNS)
    ap.add_argument("--n", type=int, default=16, help="generations per design")
    ap.add_argument("--temp", type=float, default=0.8)
    ap.add_argument("--max-tokens", type=int, default=768)
    ap.add_argument("--n-stim", type=int, default=512, help="oracle stimulus len")
    args = ap.parse_args()

    prompts = probe_prompts(set(args.designs))
    missing = set(args.designs) - set(prompts)
    if missing:
        print(f"[warn] no corpus entry for: {sorted(missing)}")
    print(f"probing {len(prompts)} designs, n={args.n} each "
          f"(oracle verdict, corpus-format prompts)")

    tok = AutoTokenizer.from_pretrained(args.base)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        args.base, torch_dtype=torch.float16, device_map={"": 0})
    model.eval()

    results = {}
    if args.adapter:
        from peft import PeftModel
        model = PeftModel.from_pretrained(model, args.adapter, is_trainable=False)
        # base = same weights with the adapter disabled (matched comparison)
        with model.disable_adapter():
            results["base"] = run_probe("BASE (adapter disabled)", model, tok,
                                        prompts, args.n, args.temp,
                                        args.max_tokens, args.n_stim)
        results["sft"] = run_probe("SFT (adapter enabled)", model, tok, prompts,
                                   args.n, args.temp, args.max_tokens, args.n_stim)
    else:
        results["base"] = run_probe("BASE", model, tok, prompts, args.n,
                                    args.temp, args.max_tokens, args.n_stim)

    print("\n================ SUMMARY ================")
    for k, v in results.items():
        print(f"  {k:5s} overall correct-rate: {v:.1f}%")
    if "sft" in results:
        d = results["sft"] - results["base"]
        print(f"  delta (SFT - base): {d:+.1f} pp")
        print("  GATE: if SFT correct-rate is now well above the ~2% baseline, "
              "GRPO on the V2 oracle has a foothold. If not, diversify the "
              "corpus / reconsider the base before spending GRPO+EDA time.")


if __name__ == "__main__":
    main()
