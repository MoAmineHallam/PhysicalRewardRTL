#!/usr/bin/env python3
"""
run_verilogeval_passk.py  -  VerilogEval pass@k (n samples, temp 0.8).

Greedy (temp 0.1) eval showed GRPO-v3 fixed 8 problems and broke 8 — the
distribution moved but the argmax nets to zero. pass@k at sampling
temperature is the standard VerilogEval protocol and the right lens for
that: run BOTH models through THIS script (same dtype, same decoding) and
compare pass@1/5/10.

Per problem: n samples in one batched generate() (fp16, single GPU, stop
at 'endmodule' — the build_dataset fast path), each compiled+simulated
against the official ref/test (same harness logic as run_verilogeval.py).
Unbiased pass@k:  1 - C(n-c, k)/C(n, k).

Run from /zeng_gk/Amine/mas:
    python fpga/run_verilogeval_passk.py --tag base
    python fpga/run_verilogeval_passk.py --adapter grpo_v3 --tag grpo_v3
    python fpga/run_verilogeval_passk.py --tag base --summarize-only

Appends fpga/passk_<tag>.jsonl (one record per sample; resume skips
problems that already have >= n samples) and prints the summary.
"""

import os
import sys
import re
import json
import glob
import math
import time
import argparse
import tempfile
import subprocess
import collections
import concurrent.futures as cf

os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("HF_HUB_OFFLINE", "1")

HERE = os.path.dirname(os.path.abspath(__file__))
LLM_DIR = "/zeng_gk/Amine/mas"
DATASET = "/zeng_gk/Amine/verilog-eval/dataset_spec-to-rtl"
SIM_TIMEOUT = 60

# identical to run_verilogeval.py
SYSTEM = ("You are an expert Verilog RTL designer. Write synthesizable "
          "Verilog-2001. The module MUST be named TopModule with exactly "
          "the ports given in the prompt. Return only the Verilog module, "
          "no markdown, no explanation.")


def strip_fences(rtl):
    """First-endmodule variant (matches run_verilogeval_ft.py)."""
    bt = chr(96)
    rtl = rtl.replace(bt * 3 + "verilog", "").replace(bt * 3, "")
    mm = re.search(r"\bmodule\s+\w+\s*[(#;]", rtl)
    if mm:
        rtl = rtl[mm.start():]
    rtl = rtl.strip()
    if "endmodule" in rtl:
        rtl = rtl[:rtl.index("endmodule") + len("endmodule")]
    return rtl


def judge(rtl, ref_f, test_f):
    """(status, detail) — same verdicts as run_verilogeval.py."""
    with tempfile.TemporaryDirectory() as wd:
        cand = os.path.join(wd, "cand.sv")
        out = os.path.join(wd, "sim.out")
        with open(cand, "w") as f:
            f.write(rtl)
        c = subprocess.run(["iverilog", "-g2012", "-o", out,
                            cand, ref_f, test_f],
                           capture_output=True, text=True)
        if c.returncode != 0:
            return "compile_fail", c.stderr.strip().split("\n")[0][:100]
        try:
            s = subprocess.run(["vvp", out], capture_output=True, text=True,
                               timeout=SIM_TIMEOUT)
        except subprocess.TimeoutExpired:
            return "sim_timeout", ""
    log = s.stdout + s.stderr
    m = re.search(r"Mismatches:\s*(\d+)\s*in\s*(\d+)\s*samples", log)
    if not m:
        return "no_verdict", log.strip().split("\n")[-1][:100]
    errs, samples = int(m.group(1)), int(m.group(2))
    if samples > 0 and errs == 0:
        return "PASS", ""
    return "fail", f"{errs}/{samples} mismatches"


def pass_at_k(n, c, k):
    if n - c < k:
        return 1.0
    return 1.0 - math.comb(n - c, k) / math.comb(n, k)


def load_done(out_path):
    counts = collections.Counter()
    if os.path.exists(out_path):
        for line in open(out_path):
            try:
                counts[json.loads(line)["problem"]] += 1
            except (ValueError, KeyError):
                pass
    return counts


def summarize(out_path, n):
    by_prob = collections.defaultdict(list)
    for line in open(out_path):
        r = json.loads(line)
        by_prob[r["problem"]].append(r["status"])
    probs = sorted(by_prob)
    tot = len(probs)
    p1 = p5 = p10 = comp = 0.0
    for pb in probs:
        st = by_prob[pb][:n]
        c = st.count("PASS")
        m = len(st)
        comp += sum(s in ("PASS", "fail") for s in st) / m
        p1 += pass_at_k(m, c, 1)
        p5 += pass_at_k(m, c, min(5, m))
        p10 += pass_at_k(m, c, min(10, m))
    print("=" * 50)
    print(f"Problems       : {tot}")
    print(f"Compile rate   : {100 * comp / tot:.1f}%")
    print(f"pass@1         : {100 * p1 / tot:.1f}%")
    print(f"pass@5         : {100 * p5 / tot:.1f}%")
    print(f"pass@10        : {100 * p10 / tot:.1f}%")
    print("=" * 50)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--adapter", default=None,
                    help="LoRA adapter dir (omit = base model)")
    ap.add_argument("--tag", required=True,
                    help="output name: fpga/passk_<tag>.jsonl")
    ap.add_argument("--n", type=int, default=10, help="samples per problem")
    ap.add_argument("--gen-batch", type=int, default=5,
                    help="samples generated per forward batch (caps peak "
                         "KV-cache memory; 5 fits a 7B fp16 on a 32GB V100)")
    ap.add_argument("--temp", type=float, default=0.8)
    ap.add_argument("--max-tokens", type=int, default=1024)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--summarize-only", action="store_true")
    args = ap.parse_args()

    out_path = os.path.join(HERE, f"passk_{args.tag}.jsonl")
    if args.summarize_only:
        summarize(out_path, args.n)
        return

    probs = sorted(set(
        os.path.basename(p).replace("_prompt.txt", "")
        for p in glob.glob(os.path.join(DATASET, "*_prompt.txt"))))
    probs = probs[args.start:]
    if args.limit is not None:
        probs = probs[:args.limit]
    done = load_done(out_path)

    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM
    base_path = os.environ.get("RTLCODER_PATH",
                               os.path.join(LLM_DIR, "rtlcoder"))
    print(f"[LLM] {base_path} (fp16, single GPU, batched)"
          + (f" + adapter {args.adapter}" if args.adapter else " [base]"),
          flush=True)
    tok = AutoTokenizer.from_pretrained(base_path)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        base_path, torch_dtype=torch.float16, device_map={"": 0})
    if args.adapter:
        from peft import PeftModel
        model = PeftModel.from_pretrained(model, args.adapter,
                                          is_trainable=False)
    model.eval()

    def gen(spec, k):
        chat = tok.apply_chat_template(
            [{"role": "system", "content": SYSTEM},
             {"role": "user", "content": spec}],
            tokenize=False, add_generation_prompt=True)
        inputs = tok(chat, return_tensors="pt",
                     return_token_type_ids=False).to("cuda:0")
        plen = inputs["input_ids"].shape[1]
        # Generate in sub-batches: a 7B model's KV cache for k=20 wide x
        # 1024 new tokens on the long-prompt FSM problems blows past 32 GiB.
        # Chunking caps peak memory at gen_batch-wide while keeping all k
        # samples i.i.d. (do_sample with no fixed seed per chunk).
        outs = []
        for start in range(0, k, args.gen_batch):
            chunk = min(args.gen_batch, k - start)
            with torch.inference_mode():
                out = model.generate(
                    **inputs, max_new_tokens=args.max_tokens,
                    do_sample=True, temperature=args.temp,
                    num_return_sequences=chunk,
                    stop_strings=["endmodule"], tokenizer=tok,
                    pad_token_id=tok.eos_token_id)
            outs.extend(tok.decode(seq[plen:], skip_special_tokens=True)
                        for seq in out)
            del out
            torch.cuda.empty_cache()
        return outs

    print(f"{len(probs)} problems, {args.n} samples each -> {out_path}",
          flush=True)
    with open(out_path, "a") as fout:
        for i, pb in enumerate(probs):
            need = args.n - done.get(pb, 0)
            if need <= 0:
                continue
            ref_f = os.path.join(DATASET, pb + "_ref.sv")
            test_f = os.path.join(DATASET, pb + "_test.sv")
            if not (os.path.exists(ref_f) and os.path.exists(test_f)):
                continue
            spec = open(os.path.join(DATASET, pb + "_prompt.txt")).read()
            t0 = time.time()
            rtls = [strip_fences(raw) for raw in gen(spec, need)]
            with cf.ThreadPoolExecutor(max_workers=min(8, need)) as ex:
                verdicts = list(ex.map(
                    lambda r: judge(r, ref_f, test_f), rtls))
            for rtl, (status, detail) in zip(rtls, verdicts):
                fout.write(json.dumps({
                    "problem": pb, "status": status, "detail": detail,
                    "rtl": rtl}) + "\n")
            fout.flush()
            npass = sum(s == "PASS" for s, _ in verdicts)
            print(f"[{i + 1}/{len(probs)}] {pb}: {npass}/{need} pass "
                  f"{time.time() - t0:.0f}s", flush=True)

    summarize(out_path, args.n)


if __name__ == "__main__":
    main()
