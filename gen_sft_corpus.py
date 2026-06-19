#!/usr/bin/env python3
"""
gen_sft_corpus.py  -  V2 Stage 1: build an SFT warm-start corpus of CORRECT,
diverse (spec -> RTL) pairs, every one verified by the V2 oracle.

Why: the cross-model probe showed base models write these accelerators correctly
at ~2% -> RL has no foothold (RL refines competence, can't create it). The fix is
SFT warm-start (the supervisor's own roadmap step 1). This generates the corpus:
for a parameter grid over the single-input accelerator families, emit each design
in MULTIPLE coding styles (unpipelined reference + pipelined), so the model learns
both correctness AND implementation diversity (the diversity that later gives the
silicon-Fmax RL its headroom). Every pair is oracle-verified (I/O-equivalence under
directed+random stimulus) before it enters the corpus -- no incorrect training data.

Output: sft_corpus.jsonl  {"design","family","style","prompt","completion"} per line.
Prompt = natural-language spec + exact module interface; completion = the RTL.

Run anywhere with iverilog:  python gen_sft_corpus.py --out sft_corpus.jsonl
"""

import os
import re
import json
import argparse

import gen_accelerator_catalog as GAC
import oracle

HERE = os.path.dirname(os.path.abspath(__file__))


def header_of(rtl):
    """Extract the `module ... );` interface block to put in the prompt."""
    m = re.search(r"(?s)(module\s+\w+\s*\(.*?\);)", rtl)
    return m.group(1) if m else ""


def make_prompt(spec, rtl):
    return (spec.rstrip() + "\n\nUse exactly this module interface "
            "(port names and widths must match):\n\n" + header_of(rtl) +
            "\n\nWrite standard synthesizable Verilog-2001. Active-low rst_n "
            "clears the outputs; outputs are registered on posedge clk.")


def designs():
    """Yield (design_name, family, spec_text, {style: rtl_text}) over a grid.

    Each design is emitted in MULTIPLE oracle-verified correct styles so SFT
    learns implementation diversity (the headroom the silicon-Fmax RL exploits):
      fir/firr : array+loop reference, pipelined, unrolled named-register form
      poly     : combinational Horner chain, pipelined, inline nested form
      cordic   : unrolled combinational chain, pipelined
    """
    fir_taps = list(range(4, 33))                  # 4..32, every tap count
    for T in fir_taps:
        c = GAC.fir_coeffs(T); nm = f"fir{T}_8b"
        yield nm, "fir", GAC.fir_spec(nm, T), {
            "ref": GAC.fir_ref(nm, c), "pipe": GAC.fir_pipe(nm, c),
            "unrolled": GAC.fir_unrolled(nm, c)}
    for T in fir_taps:
        c = [k + 1 for k in range(T)]; nm = f"firr{T}"
        yield nm, "firr", GAC.firr_spec(nm, T), {
            "ref": GAC.fir_ref(nm, c), "pipe": GAC.fir_pipe(nm, c),
            "unrolled": GAC.fir_unrolled(nm, c)}
    for D in range(2, 11):
        c = GAC.poly_coeffs(D); nm = f"poly{D}_8b"
        yield nm, "poly", GAC.poly_spec(nm, D, c), {
            "ref": GAC.poly_ref(nm, c), "pipe": GAC.poly_pipe(nm, c),
            "inline": GAC.poly_inline(nm, c)}
    for N in [6, 8, 10, 12, 14, 16, 18]:
        atan, x0 = GAC.cordic_tables(N); nm = f"cordic{N}"
        yield nm, "cordic", GAC.cordic_spec(nm, N), {
            "ref": GAC.cordic_ref(nm, N, atan, x0),
            "pipe": GAC.cordic_pipe(nm, N, atan, x0)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "sft_corpus.jsonl"))
    ap.add_argument("--n", type=int, default=512, help="oracle stimulus length")
    args = ap.parse_args()

    rows, kept, rejected = [], 0, 0
    by_fam = {}
    for name, fam, spec, styles in designs():
        for style, rtl in styles.items():
            try:
                r = oracle.score(rtl, name, n=args.n)
            except Exception as e:
                print(f"  [skip] {name}/{style}: {e}")
                rejected += 1
                continue
            if not r["correct"]:
                print(f"  [REJECT] {name}/{style}: match={r['match']} "
                      f"compiled={r['compiled']} (oracle gate)")
                rejected += 1
                continue
            rows.append({"design": name, "family": fam, "style": style,
                         "prompt": make_prompt(spec, rtl), "completion": rtl})
            kept += 1
            by_fam[fam] = by_fam.get(fam, 0) + 1

    with open(args.out, "w") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")
    print(f"\nSFT corpus: {kept} oracle-verified pairs ({rejected} rejected) "
          f"-> {args.out}")
    print("per family:", by_fam)
    print("Every completion is I/O-equivalence-verified correct (no bad training "
          "data). Next: SFT the base model on this, then GRPO on the V2 oracle.")


if __name__ == "__main__":
    main()
