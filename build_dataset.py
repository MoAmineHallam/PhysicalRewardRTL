#!/usr/bin/env python3
"""
build_dataset.py  -  Stage 7 RL dataset builder (manifest-driven, all designs).

For every hardware-validated design (hw_bad.json["good"], from stage 6):
generate N candidates with RTLCoder from the design's spec.txt, score each
with score_candidate (dense Hamming reward against the silicon-certified
golden), append JSONL records.

Runs on the GPU server (needs /zeng_gk/Amine/mas on sys.path for llm.py).

Usage:
    python build_dataset.py                          # all good designs
    python build_dataset.py --n 20 --temp 0.9
    python build_dataset.py --designs mod7_counter acc2to8
    python build_dataset.py --start 0 --limit 200    # shard a long run
    python build_dataset.py --out dataset.jsonl      # append + resume:
                                                     # designs that already
                                                     # have >= n records are
                                                     # skipped

Record format (one JSON object per line):
    {"design": str, "family": str, "reward": float, "compile_ok": bool,
     "rtl": str}
reward is 0.0 when the candidate fails to compile/simulate.
"""

import os
import sys
import json
import argparse
import collections

import score_candidate as SC

HERE = os.path.dirname(os.path.abspath(__file__))
LLM_DIR = "/zeng_gk/Amine/mas"
sys.path.insert(0, LLM_DIR)


def extract_verilog(text, module_name):
    """Extract first complete Verilog module from LLM output."""
    import re
    m = re.search(rf"(?s)(module\s+{re.escape(module_name)}\b.*?endmodule)",
                  text)
    if m:
        return m.group(1)
    m = re.search(r"(?s)(module\s+\w+\b.*?endmodule)", text)
    if m:
        return m.group(1)
    return None


def make_prompt(rec, spec):
    """Spec + the exact module interface from design.v.

    The generated spec.txt files are one-liners that don't pin down port
    names; the scoring testbench connects by name, so candidates with
    invented ports fail to compile. Giving the interface is legitimate --
    it's part of the problem statement, not the solution.
    """
    import re
    src = open(os.path.join(SC.RTL_LIB, rec["name"], "design.v")).read()
    m = re.search(rf"(?s)(module\s+{re.escape(rec['name'])}\b.*?\);)", src)
    header = m.group(1)
    return (f"{spec}\n\n"
            f"Use exactly this module interface (port names and widths "
            f"must match):\n\n{header}\n\n"
            f"Active-low reset rst_n clears the outputs; outputs are "
            f"registered on posedge clk.\n")


def load_pool(hw_report):
    """Hardware-validated designs that have a spec.txt, manifest order."""
    man = SC.load_manifest()
    good = SC.load_good_names(hw_report)
    pool = []
    for name, rec in man.items():
        if name not in good:
            continue
        spec_path = os.path.join(SC.RTL_LIB, name, "spec.txt")
        if not os.path.exists(spec_path):
            print(f"[warn] {name}: spec.txt missing, skipped", file=sys.stderr)
            continue
        pool.append((rec, make_prompt(rec, open(spec_path).read())))
    return pool


def existing_counts(out_path):
    counts = collections.Counter()
    if os.path.exists(out_path):
        for line in open(out_path):
            try:
                counts[json.loads(line)["design"]] += 1
            except (ValueError, KeyError):
                pass
    return counts


def get_generator(args):
    """Return gen(prompt, k) -> list[str] of k candidate completions.

    backend 'local' (default): batched fp16 generation on one GPU.
      - all k samples in ONE generate() call (num_return_sequences=k)
      - fp16, not bf16: V100s have no bf16 hardware, PyTorch emulates it
      - whole model on cuda:0 (7B fp16 ~14GB): device_map='auto' sharding
        across 2 GPUs makes each wait on the other
      - stops at 'endmodule' instead of rambling to the token cap
    backend 'llm': the original sequential llm.coder_call (fallback).
    """
    if args.backend == "llm":
        from llm import coder_call

        def gen(prompt, k):
            outs = []
            for _ in range(k):
                outs.append(coder_call(
                    [{"role": "user", "content": prompt}],
                    max_tokens=args.max_tokens, temperature=args.temp))
            return outs
        return gen

    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM
    path = os.environ.get("RTLCODER_PATH", os.path.join(LLM_DIR, "rtlcoder"))
    print(f"[LLM] loading RTLCoder from {path} (fp16, single GPU, batched)",
          flush=True)
    tok = AutoTokenizer.from_pretrained(path)
    model = AutoModelForCausalLM.from_pretrained(
        path, torch_dtype=torch.float16, device_map={"": 0})
    model.eval()

    def _clean(text):
        if "endmodulemodule" in text:
            return text.split("endmodulemodule")[0] + "endmodule"
        idx = text.rfind("endmodule")
        if idx >= 0:
            return text[:idx + len("endmodule")]
        return text

    def gen(prompt, k):
        chat = tok.apply_chat_template(
            [{"role": "user", "content": prompt}],
            tokenize=False, add_generation_prompt=True)
        inputs = tok(chat, return_tensors="pt",
                     return_token_type_ids=False).to("cuda:0")
        with torch.inference_mode():
            out = model.generate(
                **inputs,
                max_new_tokens=args.max_tokens,
                do_sample=args.temp > 0,
                temperature=args.temp,
                num_return_sequences=k,
                stop_strings=["endmodule"],
                tokenizer=tok,
                pad_token_id=tok.eos_token_id)
        plen = inputs["input_ids"].shape[1]
        return [_clean(tok.decode(seq[plen:], skip_special_tokens=True))
                for seq in out]
    return gen


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=20,
                    help="candidates per design")
    ap.add_argument("--temp", type=float, default=0.9)
    ap.add_argument("--max-tokens", type=int, default=512)
    ap.add_argument("--backend", choices=["local", "llm"], default="local",
                    help="local = batched fp16 single-GPU (fast); "
                         "llm = original llm.coder_call")
    ap.add_argument("--cycles", type=int, default=SC.N_CYCLES_DEFAULT,
                    help="simulation cycles per score")
    ap.add_argument("--out", default="dataset.jsonl")
    ap.add_argument("--hw-report", default=SC.HW_REPORT)
    ap.add_argument("--designs", nargs="*", default=None,
                    help="restrict to these design names")
    ap.add_argument("--start", type=int, default=0,
                    help="skip the first START designs of the pool")
    ap.add_argument("--limit", type=int, default=None,
                    help="process at most LIMIT designs")
    args = ap.parse_args()

    gen = get_generator(args)

    pool = load_pool(args.hw_report)
    if args.designs:
        keep = set(args.designs)
        pool = [(r, s) for r, s in pool if r["name"] in keep]
    pool = pool[args.start:]
    if args.limit is not None:
        pool = pool[:args.limit]
    done = existing_counts(args.out)
    manifest = SC.load_manifest()

    print(f"pool: {len(pool)} hardware-validated designs, "
          f"{args.n} candidates each -> {args.out}", flush=True)

    with open(args.out, "a") as fout:
        for di, (rec, spec) in enumerate(pool):
            name = rec["name"]
            need = args.n - done.get(name, 0)
            if need <= 0:
                continue
            print(f"[{di + 1}/{len(pool)}] {name}: generating {need}",
                  flush=True)
            stats = []
            try:
                raws = gen(spec, need)
            except Exception as e:
                print(f"   generation failed: {e}", file=sys.stderr)
                continue
            for raw in raws:
                rtl = extract_verilog(raw, name)
                if rtl is None:
                    rtl, reward, ok = raw[-2000:], 0.0, False
                else:
                    rtl = rtl.encode("ascii", errors="replace").decode("ascii")
                    try:
                        reward = SC.score_rtl(rtl, name, args.cycles, manifest)
                        ok = True
                    except RuntimeError:
                        reward, ok = 0.0, False
                fout.write(json.dumps({
                    "design": name, "family": rec["family"],
                    "reward": reward, "compile_ok": ok, "rtl": rtl,
                }) + "\n")
                fout.flush()
                stats.append(reward)
            if stats:
                print(f"   rewards: mean={sum(stats) / len(stats):.3f} "
                      f"max={max(stats):.3f} "
                      f"compile_ok={sum(s > 0 for s in stats)}/{len(stats)}",
                      flush=True)

    print("done.")


if __name__ == "__main__":
    main()
