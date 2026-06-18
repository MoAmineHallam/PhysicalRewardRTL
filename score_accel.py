#!/usr/bin/env python3
"""
score_accel.py  -  Correctness scorer for the accelerator catalog.

The accelerator designs (gen_accelerator_catalog.py) carry their reference model
as rtl_library/<design>/golden.py (compute_golden), NOT as a manifest golden_body
like the original 966-design catalog. This scores a candidate RTL string against
that golden the same way the silicon harness does: drive x=cnt[7:0], capture the
16-bit registered output for N cycles, and take the best masked match over a
small TWO-SIDED registration shift (so pipeline latency is absorbed).

reward = fraction of cycles matching the golden (0 if it won't compile / wrong
module name / no output). Used by gen_accel_candidates.py (keep reward>=0.999)
and reusable as the correctness gate for the Phase-3 RL.

CLI (score one file):
    python score_accel.py --design fir16_8b --file cand.v
"""

import os
import re
import subprocess
import tempfile
import importlib.util

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RTL_LIB = os.path.join(HERE, "rtl_library")
N_CYCLES_DEFAULT = 400
MAX_SHIFT_DEFAULT = 24

# Instruct models (qwen-coder etc.) default to SystemVerilog -- '{...} assignment
# patterns, foreach, inline `for (integer i...)`, logic -- which the fast
# correctness gate (iverilog -g2012) cannot compile (Vivado would). Steer to the
# Verilog-2001 subset iverilog accepts so the gate measures the model's LOGIC,
# not its dialect. (All synthesizable; nothing here changes the design's behaviour.)
V2001_SUFFIX = (
    "\n\nWrite standard synthesizable Verilog-2001 ONLY -- it must compile under "
    "Icarus Verilog (iverilog -g2012). Do NOT use SystemVerilog constructs: no "
    "'{...} assignment patterns, no `foreach`, no `logic`, no inline "
    "`for (integer i = ...)`. Declare any loop variable as `integer i;` before the "
    "always block and write `for (i = 0; i < N; i = i + 1)`. Initialise arrays "
    "element by element. Output only the module (no testbench, no comments needed)."
)


def load_golden(design, n):
    path = os.path.join(RTL_LIB, design, "golden.py")
    spec = importlib.util.spec_from_file_location("g_" + design, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.compute_golden(n).astype(np.uint16)


def _tb(module, n):
    return f"""`timescale 1ns/1ps
module tb;
  reg clk=0, rst_n=0; reg [31:0] cnt=0; wire [15:0] y;
  {module} dut(.clk(clk), .rst_n(rst_n), .x(cnt[7:0]), .y(y));
  always #5 clk=~clk;
  integer i;
  initial begin
    rst_n=0; cnt=0; @(posedge clk); @(posedge clk); rst_n=1;
    for (i=0;i<{n};i=i+1) begin @(posedge clk); cnt=cnt+1; $display("%0d", y); end
    $finish;
  end
endmodule
"""


def _best_shift(hw, g, mask=0xFFFF, ms=MAX_SHIFT_DEFAULT):
    if hw is None or len(hw) < 32:
        return 0.0
    a0 = (hw & mask).astype(np.uint16)
    g0 = (g & mask).astype(np.uint16)
    best = 0.0
    for sh in range(ms + 1):
        for a, b in ((a0, g0[sh:]), (a0[sh:], g0)):
            k = min(len(a), len(b))
            if k < 32:
                continue
            s = float(np.mean(a[:k] == b[:k]))
            if s > best:
                best = s
    return best


def score_rtl(rtl, design, n=N_CYCLES_DEFAULT, max_shift=MAX_SHIFT_DEFAULT):
    """Compile candidate + TB with iverilog, run, compare to golden. 0 on any
    failure (won't compile, wrong/missing module name, no output)."""
    if not re.search(r"\bmodule\s+" + re.escape(design) + r"\b", rtl):
        return 0.0
    g = load_golden(design, n + max_shift + 8)
    with tempfile.TemporaryDirectory() as wd:
        cand = os.path.join(wd, "cand.v")
        tb = os.path.join(wd, "tb.v")
        vvp = os.path.join(wd, "a.vvp")
        open(cand, "w").write(rtl)
        open(tb, "w").write(_tb(design, n))
        c = subprocess.run(["iverilog", "-g2012", "-o", vvp, cand, tb],
                           capture_output=True, text=True)
        if c.returncode != 0:
            return 0.0
        r = subprocess.run(["vvp", vvp], capture_output=True, text=True)
        vals = [int(v) for v in r.stdout.split()
                if v.strip().isdigit() and 0 <= int(v) < 65536]
        if len(vals) < 32:
            return 0.0
        return _best_shift(np.array(vals, dtype=np.uint16), g)


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--design", required=True)
    ap.add_argument("--file", required=True)
    ap.add_argument("--n", type=int, default=N_CYCLES_DEFAULT)
    args = ap.parse_args()
    rtl = open(args.file).read()
    print(f"{args.design}  {args.file}  reward={score_rtl(rtl, args.design, args.n):.4f}")


if __name__ == "__main__":
    main()
