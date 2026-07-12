#!/usr/bin/env python3
"""
vet_families.py  -  cheap GO/NO-GO probe for NEW accelerator families.

Before spending catalog/SFT/GRPO effort on a family, it must pass two gates:
  1. FOOTHOLD  -- the styles are simple enough that a 7B can plausibly learn
     them (we hand-write them here; if *we* can't write them small, skip);
  2. HEADROOM  -- different implementation styles synthesize to genuinely
     different Fmax (else the Fmax-RL has nothing to optimize).

This script hand-writes 2 styles per candidate design, proves them
I/O-equivalent to a python reference with iverilog (gate 1 sanity + no bad
templates), and emits rtl/family_vet/*.sv + fmax_manifest.json for run_ppa.
The Vivado spread per design is gate 2: want fast/slow >= ~1.5-2x to build
the family for real.

Candidates (same clk/rst_n/x[7:0]/y[15:0] interface -> oracle TB reused as-is):
  iir{N}  -- order-N IIR: y[n] = (sum b_k x[n-k] + (9*y[n-1]>>4) + (5*y[n-2]>>4))
             mod 2^16. FEEDBACK makes this structurally different from FIR.
             styles: ref (one big combinational sum, path grows with N)
                     tr  (transposed feedforward chain + tiny feedback stage,
                          path ~constant in N)
  med{W}  -- streaming median-of-W (odd W): y[n] = median(x[n..n-W+1]).
             NO multipliers at all -- pure comparator networks.
             styles: comb (full odd-even sort network combinational, deep)
                     pipe (same network cut into ~3-pass pipeline stages)

    sandbox: python vet_families.py           # generate + iverilog-verify
    laptop : python run_ppa.py --dir rtl/family_vet --out rtl/family_vet/ppa.jsonl \
                 --clk clk --period 5.0 --vivado ...
    verdict: fast vs slow real Fmax per design (this script --report reads it)
"""

import os
import json
import argparse

import numpy as np

import oracle

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "rtl", "family_vet")
MASK = 0xFFFF

# fixed feedback coefficients (with >>4: 9/16 + 5/16 < 1 -> decay-flavoured)
A1, A2 = 9, 5


def iir_coeffs(order):
    return [2 * k + 3 for k in range(order + 1)]        # b0..bN small odds


# ------------------------------------------------------------------ references
def iir_ref_py(xs, order):
    B = iir_coeffs(order)
    xd = [0] * order          # x[n-1] .. x[n-order]
    y1 = y2 = 0
    out = []
    for x in xs:
        acc = B[0] * int(x) + sum(B[k] * xd[k - 1] for k in range(1, order + 1))
        acc += (A1 * y1) >> 4
        acc += (A2 * y2) >> 4
        ynew = acc & MASK
        y2, y1 = y1, ynew
        xd = [int(x)] + xd[:-1]
        out.append(ynew)
    return np.array(out, dtype=np.uint16)


def med_ref_py(xs, W):
    win = [0] * W
    out = []
    for x in xs:
        win = [int(x)] + win[:-1]
        out.append(sorted(win)[W // 2])
    return np.array(out, dtype=np.uint16)


# ------------------------------------------------------------------ IIR RTL
def iir_rtl_ref(mod, order):
    B = iir_coeffs(order)
    taps = " + ".join([f"{B[0]}*x"] +
                      [f"{B[k]}*xd{k}" for k in range(1, order + 1)])
    decl = "\n".join(f"  reg [7:0] xd{k};" for k in range(1, order + 1))
    clr = " ".join(f"xd{k}<=0;" for k in range(1, order + 1))
    shift = " ".join(f"xd{k}<=xd{k-1};" for k in range(order, 1, -1))
    return f"""module {mod} (
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);
{decl}
  reg [15:0] y2;
  wire [31:0] acc = {taps} + (({A1}*y)>>4) + (({A2}*y2)>>4);
  always @(posedge clk) begin
    if (!rst_n) begin y<=0; y2<=0; {clr} end
    else begin
      y <= acc[15:0];
      y2 <= y;
      {shift} xd1 <= x;
    end
  end
endmodule
"""


def iir_rtl_tr(mod, order):
    """Transposed feedforward chain: partial sums registered, so the output
    stage is one mult+add plus the (small) feedback adds -- path ~const in N."""
    B = iir_coeffs(order)
    decl = "\n".join(f"  reg [15:0] r{k};" for k in range(1, order + 1))
    clr = " ".join(f"r{k}<=0;" for k in range(1, order + 1))
    upd = "\n      ".join(
        [f"r{k} <= ({B[k]}*x + r{k+1}) & 16'hFFFF;" for k in range(1, order)] +
        [f"r{order} <= ({B[order]}*x) & 16'hFFFF;"])
    return f"""module {mod} (
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);
{decl}
  reg [15:0] y2;
  wire [31:0] acc = {B[0]}*x + r1 + (({A1}*y)>>4) + (({A2}*y2)>>4);
  always @(posedge clk) begin
    if (!rst_n) begin y<=0; y2<=0; {clr} end
    else begin
      y <= acc[15:0];
      y2 <= y;
      {upd}
    end
  end
endmodule
"""


# ------------------------------------------------------------------ median RTL
def _sort_passes(W):
    """Odd-even transposition sort: W passes of adjacent compare-swaps."""
    return [[(i, i + 1) for i in range(p % 2, W - 1, 2)] for p in range(W)]


def _emit_pass(lines, prev, nxt, pairs, W):
    swapped = set()
    for i, j in pairs:
        lines.append(f"  wire [7:0] {nxt}_{i} = ({prev}_{i} <= {prev}_{j}) ? "
                     f"{prev}_{i} : {prev}_{j};")
        lines.append(f"  wire [7:0] {nxt}_{j} = ({prev}_{i} <= {prev}_{j}) ? "
                     f"{prev}_{j} : {prev}_{i};")
        swapped |= {i, j}
    for k in range(W):
        if k not in swapped:
            lines.append(f"  wire [7:0] {nxt}_{k} = {prev}_{k};")


def med_rtl(mod, W, pipe):
    """Median-of-W. Window = (x, w0..w{W-2}) so latency is 1 (comb) or
    1+n_stages (pipe); the oracle-style aligner absorbs the offset."""
    passes = _sort_passes(W)
    lines = [f"module {mod} (",
             "  input clk, input rst_n, input [7:0] x, output reg [15:0] y",
             ");"]
    for k in range(W - 1):
        lines.append(f"  reg [7:0] w{k};")
    # layer 0 = current window
    lines.append("  wire [7:0] l0_0 = x;")
    for k in range(W - 1):
        lines.append(f"  wire [7:0] l0_{k+1} = w{k};")

    stage_regs, prev, li = [], "l0", 0
    for p, pairs in enumerate(passes):
        li += 1
        _emit_pass(lines, prev, f"l{li}", pairs, W)
        prev = f"l{li}"
        # pipeline cut every 3 passes (not after the last pass)
        if pipe and (p + 1) % 3 == 0 and p != len(passes) - 1:
            sname = f"s{len(stage_regs)}"
            for k in range(W):
                lines.append(f"  reg [7:0] {sname}_{k};")
            stage_regs.append((sname, prev))
            prev = sname

    lines.append("  always @(posedge clk) begin")
    lines.append("    if (!rst_n) begin")
    lines.append("      y<=0; " + " ".join(f"w{k}<=0;" for k in range(W - 1)))
    for sname, _ in stage_regs:
        lines.append("      " + " ".join(f"{sname}_{k}<=0;" for k in range(W)))
    lines.append("    end else begin")
    lines.append(f"      y <= {{8'b0, {prev}_{W//2}}};")
    for sname, src in stage_regs:
        lines.append("      " + " ".join(f"{sname}_{k}<={src}_{k};"
                                         for k in range(W)))
    lines.append("      " + " ".join(f"w{k}<=w{k-1};"
                                     for k in range(W - 2, 0, -1)) + " w0<=x;")
    lines.append("    end\n  end\nendmodule\n")
    return "\n".join(lines)


# ------------------------------------------------------------------ vet plan
def plan():
    """[(module, design, family, style, rtl_text, reference_fn)]"""
    out = []
    for N in (4, 8, 12):
        ref = (lambda n: (lambda xs: iir_ref_py(xs, n)))(N)
        out.append((f"vet_iir{N}_ref", f"iir{N}", "iir", "ref",
                    iir_rtl_ref(f"vet_iir{N}_ref", N), ref))
        out.append((f"vet_iir{N}_tr", f"iir{N}", "iir", "transposed",
                    iir_rtl_tr(f"vet_iir{N}_tr", N), ref))
    for W in (5, 9):
        ref = (lambda w: (lambda xs: med_ref_py(xs, w)))(W)
        out.append((f"vet_med{W}_comb", f"med{W}", "med", "comb",
                    med_rtl(f"vet_med{W}_comb", W, pipe=False), ref))
        out.append((f"vet_med{W}_pipe", f"med{W}", "med", "pipe",
                    med_rtl(f"vet_med{W}_pipe", W, pipe=True), ref))
    return out


def report():
    ppa = os.path.join(OUT_DIR, "ppa.jsonl")
    man = json.load(open(os.path.join(OUT_DIR, "fmax_manifest.json")))
    fmax = {}
    for line in open(ppa):
        try:
            p = json.loads(line)
        except ValueError:
            continue
        if p.get("compiled"):
            fmax[p["module"]] = float(p.get("fmax_mhz", 0))
    designs = {}
    for mod, info in man.items():
        designs.setdefault(info["design"], {})[info["style"]] = fmax.get(mod, 0)
    print(f"{'design':8s} {'slow-style':>16s} {'fast-style':>16s} {'ratio':>7s}  verdict")
    for d, st in sorted(designs.items()):
        slow_style = "ref" if "ref" in st else "comb"
        fast_style = "transposed" if "transposed" in st else "pipe"
        s, f = st.get(slow_style, 0), st.get(fast_style, 0)
        ratio = f / s if s else 0
        verdict = "GO (headroom)" if ratio >= 1.5 else \
                  ("marginal" if ratio >= 1.2 else "NO-GO (flat)")
        print(f"{d:8s} {slow_style:>7s} {s:7.0f} {fast_style:>9s} {f:6.0f} "
              f"{ratio:6.2f}x  {verdict}")
    print("\nGO = worth adding to the catalog (both styles already "
          "oracle-verified correct here).")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=512)
    ap.add_argument("--report", action="store_true",
                    help="read rtl/family_vet/ppa.jsonl and print the verdict")
    args = ap.parse_args()
    if args.report:
        report()
        return

    os.makedirs(OUT_DIR, exist_ok=True)
    stim = oracle.gen_stimulus(args.n, 8, seed=3)
    mani, n_ok = {}, 0
    rows = plan()
    for mod, design, family, style, rtl, ref_fn in rows:
        y_ref = ref_fn(stim)
        y_dut = oracle.run_dut(rtl, mod, stim, 8)
        frac, lat = oracle.align_score(y_dut, y_ref)
        ok = frac >= 0.999
        n_ok += ok
        print(f"  {mod:18s} ({family}/{style:10s}) match={frac:.4f} "
              f"lat={lat}  {'OK' if ok else '** FAIL **'}")
        if ok:
            open(os.path.join(OUT_DIR, mod + ".sv"), "w").write(rtl)
            mani[mod] = {"design": design, "family": family, "style": style}
    json.dump(mani, open(os.path.join(OUT_DIR, "fmax_manifest.json"), "w"),
              indent=1)
    print(f"\n{n_ok}/{len(rows)} styles verified I/O-equivalent -> {OUT_DIR}")
    print("next (laptop): python run_ppa.py --dir rtl/family_vet "
          "--out rtl/family_vet/ppa.jsonl --clk clk --period 5.0 --vivado ...\n"
          "then:          python vet_families.py --report")


if __name__ == "__main__":
    main()
