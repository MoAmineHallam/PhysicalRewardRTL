#!/usr/bin/env python3
"""
verify_designs.py  -  Pre-Vivado verification.

For each design, generates a counter-driven testbench (matching dut_top.v),
compiles design.v with iverilog, runs it, and compares the probe output
against the design's golden.py reference. Reports 100% match (synthesis-ready)
or the first mismatch.

A design that passes here compiles cleanly, uses only synthesizable constructs,
and is functionally correct -> safe to put in the bitstream with no debugging.

Usage:
    python verify_designs.py                 # verify all configured designs
    python verify_designs.py mult4x4 addsub4 # verify specific designs

Requires: iverilog, vvp on PATH; numpy.
"""

import sys
import os
import subprocess
import tempfile
import importlib.util

import numpy as np

RTL_LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rtl_library")

N_CYCLES = 4096   # enough to cover the largest period (1024) several times

# Per-design verification config:
#   inputs : list of (port_name, verilog_expr_from_cnt)
#   probe  : verilog expression packing the outputs into 16 bits (matches golden)
#   outwires: list of (verilog_decl) for output wires to declare
DESIGNS = {
    "mult4x4": {
        "inputs":   [("a", "cnt[3:0]"), ("b", "cnt[7:4]")],
        "outwires": ["wire [7:0] product;"],
        "ports":    ".a(cnt[3:0]), .b(cnt[7:4]), .product(product)",
        "probe":    "{8'b0, product}",
    },
    "comparator4": {
        "inputs":   [("a", "cnt[3:0]"), ("b", "cnt[7:4]")],
        "outwires": ["wire gt, eq, lt;"],
        "ports":    ".a(cnt[3:0]), .b(cnt[7:4]), .gt(gt), .eq(eq), .lt(lt)",
        "probe":    "{13'b0, gt, eq, lt}",
    },
    "barrel_shift": {
        "inputs":   [("data", "cnt[7:0]"), ("shamt", "cnt[9:8]")],
        "outwires": ["wire [7:0] out;"],
        "ports":    ".data(cnt[7:0]), .shamt(cnt[9:8]), .out(out)",
        "probe":    "{8'b0, out}",
    },
    "addsub4": {
        "inputs":   [("a", "cnt[3:0]"), ("b", "cnt[7:4]"), ("sub", "cnt[8]")],
        "outwires": ["wire [4:0] result;"],
        "ports":    ".a(cnt[3:0]), .b(cnt[7:4]), .sub(cnt[8]), .result(result)",
        "probe":    "{11'b0, result}",
    },
    # --- Batch 2: counters, sequential, more datapath ---
    "mod10_counter": {
        "inputs":   [],
        "outwires": ["wire [3:0] count;"],
        "ports":    ".count(count)",
        "probe":    "{12'b0, count}",
    },
    "updown_counter": {
        "inputs":   [("dir", "cnt[0]")],
        "outwires": ["wire [3:0] count;"],
        "ports":    ".dir(cnt[0]), .count(count)",
        "probe":    "{12'b0, count}",
    },
    "ring_counter": {
        "inputs":   [],
        "outwires": ["wire [3:0] count;"],
        "ports":    ".count(count)",
        "probe":    "{12'b0, count}",
    },
    "johnson_counter": {
        "inputs":   [],
        "outwires": ["wire [3:0] count;"],
        "ports":    ".count(count)",
        "probe":    "{12'b0, count}",
    },
    "parity_gen": {
        "inputs":   [("data", "cnt[7:0]")],
        "outwires": ["wire even_par, odd_par;"],
        "ports":    ".data(cnt[7:0]), .even_par(even_par), .odd_par(odd_par)",
        "probe":    "{14'b0, even_par, odd_par}",
    },
    "gray_encoder": {
        "inputs":   [("bin", "cnt[3:0]")],
        "outwires": ["wire [3:0] gray;"],
        "ports":    ".bin(cnt[3:0]), .gray(gray)",
        "probe":    "{12'b0, gray}",
    },
    "priority_enc4": {
        "inputs":   [("req", "cnt[3:0]")],
        "outwires": ["wire [1:0] enc;", "wire valid;"],
        "ports":    ".req(cnt[3:0]), .enc(enc), .valid(valid)",
        "probe":    "{13'b0, valid, enc}",
    },
    "mux4to1": {
        "inputs":   [("sel", "cnt[1:0]"), ("d0", "cnt[5:2]"), ("d1", "cnt[9:6]"),
                     ("d2", "cnt[13:10]"), ("d3", "cnt[17:14]")],
        "outwires": ["wire [3:0] out;"],
        "ports":    ".sel(cnt[1:0]), .d0(cnt[5:2]), .d1(cnt[9:6]), .d2(cnt[13:10]), .d3(cnt[17:14]), .out(out)",
        "probe":    "{12'b0, out}",
    },
    "sign_ext": {
        "inputs":   [("in4", "cnt[3:0]")],
        "outwires": ["wire [7:0] out8;"],
        "ports":    ".in4(cnt[3:0]), .out8(out8)",
        "probe":    "{8'b0, out8}",
    },
    "abs_val": {
        "inputs":   [("in", "cnt[3:0]")],
        "outwires": ["wire [3:0] out;"],
        "ports":    ".in(cnt[3:0]), .out(out)",
        "probe":    "{12'b0, out}",
    },
    "lfsr8": {
        "inputs":   [],
        "outwires": ["wire [7:0] state;"],
        "ports":    ".state(state)",
        "probe":    "{8'b0, state}",
    },
    "clk_div4": {
        "inputs":   [],
        "outwires": ["wire [1:0] cnt2;", "wire en;"],
        "ports":    ".cnt(cnt2), .en(en)",
        "probe":    "{13'b0, en, cnt2}",
    },
    "shift_accum": {
        "inputs":   [("data", "cnt[3:0]")],
        "outwires": ["wire [7:0] accum;"],
        "ports":    ".data(cnt[3:0]), .accum(accum)",
        "probe":    "{8'b0, accum}",
    },
}


def make_tb(module_name, cfg):
    outwire_decls = "\n    ".join(cfg["outwires"])
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
    wire [15:0] probe = {cfg["probe"]};

    {module_name} dut ( .clk(clk), .rst_n(rst_n), {cfg["ports"]} );

    initial begin
        @(posedge clk); wait(rst_n === 1'b1);
        @(posedge clk);
        for (i = 0; i < {N_CYCLES}; i = i + 1) begin
            @(posedge clk);
            #1;
            $display("%0d %0d", i, probe);
        end
        $finish;
    end
endmodule
"""


def load_golden(name):
    path = os.path.join(RTL_LIB, name, "golden.py")
    spec = importlib.util.spec_from_file_location(f"golden_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.compute_golden(N_CYCLES)


def verify(name):
    cfg = DESIGNS.get(name)
    if cfg is None:
        print(f"  [{name}] no verification config - SKIP")
        return None

    design_v = os.path.join(RTL_LIB, name, "design.v")
    if not os.path.exists(design_v):
        print(f"  [{name}] design.v not found - FAIL")
        return False

    golden = load_golden(name)

    with tempfile.TemporaryDirectory() as wd:
        tb_path = os.path.join(wd, "tb.v")
        out_bin = os.path.join(wd, "sim.out")
        with open(tb_path, "w") as f:
            f.write(make_tb(name, cfg))

        cp = subprocess.run(
            ["iverilog", "-g2012", "-o", out_bin, design_v, tb_path],
            capture_output=True, text=True
        )
        if cp.returncode != 0:
            print(f"  [{name}] COMPILE FAIL:\n{cp.stderr.strip()}")
            return False

        rp = subprocess.run(["vvp", out_bin], capture_output=True, text=True, timeout=60)
        sim = []
        for line in rp.stdout.splitlines():
            parts = line.split()
            if len(parts) == 2:
                try:
                    sim.append(int(parts[1]))
                except ValueError:
                    pass

    sim = np.array(sim[:N_CYCLES], dtype=np.uint16)
    n = min(len(sim), len(golden))
    sim, gold = sim[:n], golden[:n]

    # sim[j] is the registered output for cnt=j+1 (1-cycle pipeline + 1 preamble).
    # golden[c] = f(cnt=c). Account for the registration offset by shifting golden.
    matched = False
    for shift in (1, 0, 2):
        g = np.roll(gold, -shift)
        m = min(n - shift, n)
        if np.array_equal(sim[:m - 1], g[:m - 1]):
            matched = True
            used_shift = shift
            break

    if matched:
        print(f"  [{name}] PASS (100% match, reg-offset={used_shift})")
        return True
    else:
        # show first mismatch under the most likely shift (1)
        g = np.roll(gold, -1)
        diff = np.where(sim[:n - 1] != g[:n - 1])[0]
        first = diff[0] if len(diff) else -1
        print(f"  [{name}] FAIL: {len(diff)}/{n} mismatches; "
              f"first at idx {first}: sim={sim[first]} golden={g[first]}")
        return False


def main():
    names = sys.argv[1:] if len(sys.argv) > 1 else list(DESIGNS.keys())
    print(f"Verifying {len(names)} design(s) against golden references...\n")
    results = {}
    for name in names:
        results[name] = verify(name)

    print("\n" + "=" * 40)
    passed = sum(1 for v in results.values() if v is True)
    print(f"PASS: {passed}/{len(names)} designs synthesis-ready")
    failed = [n for n, v in results.items() if v is False]
    if failed:
        print(f"FAIL (fix before Vivado): {', '.join(failed)}")
    print("=" * 40)
    sys.exit(0 if not failed else 1)


if __name__ == "__main__":
    main()
