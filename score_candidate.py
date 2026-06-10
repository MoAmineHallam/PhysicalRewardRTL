#!/usr/bin/env python3
"""
score_candidate.py  -  Stage 7 scoring function (manifest-driven, all designs).

Scores an LLM-generated Verilog candidate against the hardware-validated
golden waveform of one of the rtl_library designs:

  reward = max over registration shifts (0,1,2) of the bitwise Hamming
           similarity between the candidate's simulated probe stream and the
           golden stream, masked to the meaningful probe bits.  1.0 = exact.

The reference is the manifest golden_body.  Stage 6 (validate_hw.py) proved,
for every design in hw_bad.json["good"], that this sequence is bit-identical
to what the design produces on the PYNQ-Z2 fabric — so for those designs the
reference IS the silicon behaviour (use build_dataset.py / the trainer to
restrict scoring to that set).

Usage:
    python score_candidate.py <verilog_file> <design_name> [--cycles 4096]

stdout: float 0.0-1.0.  Exit 0 on success, 2 on compile/sim failure.
Importable: load_manifest(), load_good_names(), score_rtl(), score_file().
"""

import os
import sys
import json
import argparse
import tempfile
import subprocess

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RTL_LIB = os.path.join(HERE, "rtl_library")
HW_REPORT = os.path.join(HERE, "hw_bad.json")
N_CYCLES_DEFAULT = 4096
SIM_TIMEOUT = 60


def load_manifest():
    man = json.load(open(os.path.join(RTL_LIB, "manifest.json")))
    return {r["name"]: r for r in man}


def load_good_names(report_path=HW_REPORT):
    """Designs whose golden was bit-exactly confirmed on silicon (stage 6)."""
    rep = json.load(open(report_path))
    return set(rep["good"])


def golden_from_body(body, n):
    fixed = ("def _g(n):\n"
             "    import numpy as np\n"
             "    out = []\n"
             "    for c in range(n):\n"
             + body.rstrip("\n") + "\n"
             "        out.append(val & 0xFFFF)\n"
             "    return np.array(out, dtype=np.uint16)\n")
    ns = {}
    exec(fixed, ns)
    return ns["_g"](n)


def make_tb(rec, n_cycles):
    """Counter-driven testbench, identical drive to dut_top / verify_manifest."""
    outwire_decls = "\n    ".join(rec["outwires"])
    return f"""\
`timescale 1ns/1ps
module tb;
    integer i;
    reg clk, rst_n;
    reg [31:0] cnt;
    initial clk = 0;
    always #5 clk = ~clk;
    initial begin
        rst_n = 0; cnt = 0;
        @(posedge clk); #1; rst_n = 1;
    end
    always @(posedge clk)
        if (!rst_n) cnt <= 32'd0;
        else        cnt <= cnt + 32'd1;

    {outwire_decls}
    wire [15:0] probe = {rec["probe"]};

    {rec["name"]} dut ( .clk(clk), .rst_n(rst_n), {rec["ports"]} );

    initial begin
        @(posedge clk); wait(rst_n === 1'b1);
        @(posedge clk);
        for (i = 0; i < {n_cycles}; i = i + 1) begin
            @(posedge clk); #1;
            $display("%0d %0d", i, probe);
        end
        $finish;
    end
endmodule
"""


def simulate(verilog_path, rec, n_cycles):
    """Compile + run candidate under the counter TB; return probe samples.

    Raises RuntimeError on compile/sim failure.
    """
    with tempfile.TemporaryDirectory() as wd:
        tb_path = os.path.join(wd, "tb.v")
        out_bin = os.path.join(wd, "sim.out")
        with open(tb_path, "w") as f:
            f.write(make_tb(rec, n_cycles))
        cp = subprocess.run(["iverilog", "-g2012", "-o", out_bin,
                             verilog_path, tb_path],
                            capture_output=True, text=True)
        if cp.returncode != 0:
            raise RuntimeError("COMPILE: " +
                               cp.stderr.strip().split("\n")[0][:200])
        try:
            rp = subprocess.run(["vvp", out_bin], capture_output=True,
                                text=True, timeout=SIM_TIMEOUT)
        except subprocess.TimeoutExpired:
            raise RuntimeError("SIM TIMEOUT")
    sim = []
    for line in rp.stdout.splitlines():
        parts = line.split()
        if len(parts) == 2:
            try:
                sim.append(int(parts[1]))
            except ValueError:
                pass
    if len(sim) < n_cycles // 2:
        raise RuntimeError(f"SIM produced {len(sim)}/{n_cycles} samples")
    return np.array(sim[:n_cycles], dtype=np.uint16)


def hamming_similarity(a, b, mask):
    """Fraction of matching meaningful bits (dense reward)."""
    n = min(len(a), len(b))
    diff = (a[:n] ^ b[:n]) & mask
    bits_per = bin(mask).count("1")
    if n == 0 or bits_per == 0:
        return 0.0
    wrong = int(np.unpackbits(
        diff.astype(">u2").view(np.uint8)).sum())
    return 1.0 - wrong / (n * bits_per)


def score_sim(sim, gold, mask):
    """Best Hamming similarity over registration shifts 0/1/2.

    Candidates legitimately differ from the golden by 1-2 cycles of output
    registration (verify_manifest accepts the same shifts for the goldens
    themselves), so take the best of the three.
    """
    best = 0.0
    n = min(len(sim), len(gold))
    for shift in (1, 0, 2):
        m = n - shift
        if m <= 16:
            continue
        s = hamming_similarity(sim[:m - 1], gold[shift:shift + m - 1], mask)
        best = max(best, s)
    return best


def score_file(verilog_path, name, n_cycles=N_CYCLES_DEFAULT, manifest=None):
    rec = (manifest or load_manifest())[name]
    sim = simulate(verilog_path, rec, n_cycles)
    gold = golden_from_body(rec["golden_body"], n_cycles + 2)
    return score_sim(sim, gold, rec["probe_mask"])


def score_rtl(rtl_text, name, n_cycles=N_CYCLES_DEFAULT, manifest=None):
    with tempfile.NamedTemporaryFile(suffix=".v", mode="w",
                                     delete=False) as f:
        f.write(rtl_text)
        path = f.name
    try:
        return score_file(path, name, n_cycles, manifest)
    finally:
        os.unlink(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("verilog_file")
    ap.add_argument("design_name")
    ap.add_argument("--cycles", type=int, default=N_CYCLES_DEFAULT)
    args = ap.parse_args()

    man = load_manifest()
    if args.design_name not in man:
        print(f"unknown design: {args.design_name}", file=sys.stderr)
        sys.exit(1)
    try:
        reward = score_file(args.verilog_file, args.design_name, args.cycles,
                            man)
    except RuntimeError as e:
        print(str(e), file=sys.stderr)
        sys.exit(2)
    print(f"{reward:.6f}")


if __name__ == "__main__":
    main()
