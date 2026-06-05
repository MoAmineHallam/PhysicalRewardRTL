#!/usr/bin/env python3
"""
score_candidate.py  —  Phase 3 scoring function.

Usage:
    python score_candidate.py <verilog_file> <sel_id>

    sel_id:  0=edge_detector  1=alu_mux  2=comb_always  3=bcd_counter
             4=bit_manip      5=dff_array  6=shift_reg

Returns (stdout): float 0.0-1.0 (normalized bit-match against hw waveform)
Exit 0 on success, non-zero on compile/sim failure.
"""

import sys
import os
import subprocess
import tempfile
import re
import numpy as np

# ── paths ──────────────────────────────────────────────────────────────────────
RTL_LIB    = "/zeng_gk/Amine/mas/rtl_library"
IVERILOG   = "/usr/bin/iverilog"
N_CYCLES   = 32768

DESIGN_NAMES = [
    "edge_detector",   # 0
    "alu_mux",         # 1
    "comb_always",     # 2
    "bcd_counter",     # 3
    "bit_manip",       # 4
    "dff_array",       # 5
    "shift_reg",       # 6
]

# Bitmask of meaningful probe bits per sel_id (ignore structural padding zeros).
# probe packing:
#   0: {14'b0, cnt[8], rise}          → bits [1:0]   = 0x0003
#   1: {12'b0, result[3:0]}           → bits [3:0]   = 0x000F
#   2: {12'b0, valid, out[2:0]}       → bits [3:0]   = 0x000F
#   3: {8'b0, tens[3:0], ones[3:0]}   → bits [7:0]   = 0x00FF
#   4: {4'b0, reversed[7:0], pop[3:0]}→ bits [11:0]  = 0x0FFF
#   5: {8'b0, q[7:0]}                 → bits [7:0]   = 0x00FF
#   6: {8'b0, q[7:0]}                 → bits [7:0]   = 0x00FF
PROBE_MASKS = [0x0003, 0x000F, 0x000F, 0x00FF, 0x0FFF, 0x00FF, 0x00FF]

# ── testbench templates ────────────────────────────────────────────────────────
# Each template:
#   - declares a 32-bit free-running counter (cnt), starting at 0
#   - drives the module inputs from cnt exactly as dut_top.v does
#   - prints "$display("%0d %0d", cycle, probe);" every cycle
#   - runs for N_CYCLES cycles then $finish

_TB_HEADER = """\
`timescale 1ns/1ps
module tb;
    integer i;
    reg clk, rst_n;
    reg [31:0] cnt;

    initial clk = 0;
    always #5 clk = ~clk;   // 100 MHz

    initial begin
        rst_n = 0; cnt = 0;
        @(posedge clk); #1; rst_n = 1;
    end

    // free-running counter
    always @(posedge clk)
        if (!rst_n) cnt <= 32'd0;
        else        cnt <= cnt + 32'd1;

"""

_TB_FOOTER = """\

    // print probe every cycle for {n} cycles then stop
    initial begin
        // wait for reset to deassert and one extra cycle
        @(posedge clk); wait(rst_n === 1'b1);
        @(posedge clk);
        for (i = 0; i < {n}; i = i + 1) begin
            @(posedge clk);
            #1;
            $display("%0d %0d", i, probe);
        end
        $finish;
    end
endmodule
""".format(n=N_CYCLES)

# per-design DUT instantiation + probe wire declarations
_DUT_BLOCKS = {
    0: """\
    // sel=0  edge_detector  probe={14'b0, cnt[8], rise}
    wire rise;
    wire [15:0] probe = {14'b0, cnt[8], rise};

    edge_detector dut (
        .clk   (clk),
        .rst_n (rst_n),
        .in    (cnt[8]),
        .rise  (rise)
    );
""",
    1: """\
    // sel=1  alu_mux  probe={12'b0, result[3:0]}
    wire [3:0] result;
    wire [15:0] probe = {12'b0, result};

    alu_mux dut (
        .clk    (clk),
        .rst_n  (rst_n),
        .a      (cnt[3:0]),
        .b      (cnt[7:4]),
        .op     (cnt[10:8]),
        .result (result)
    );
""",
    2: """\
    // sel=2  comb_always  probe={12'b0, valid, out[2:0]}
    wire valid;
    wire [2:0] out;
    wire [15:0] probe = {12'b0, valid, out};

    comb_always dut (
        .clk   (clk),
        .rst_n (rst_n),
        .in    (cnt[7:0]),
        .out   (out),
        .valid (valid)
    );
""",
    3: """\
    // sel=3  bcd_counter  probe={8'b0, tens[3:0], ones[3:0]}
    wire [3:0] tens, ones;
    wire [15:0] probe = {8'b0, tens, ones};

    bcd_counter dut (
        .clk  (clk),
        .rst_n(rst_n),
        .en   (1'b1),
        .tens (tens),
        .ones (ones)
    );
""",
    4: """\
    // sel=4  bit_manip  probe={4'b0, reversed[7:0], popcount[3:0]}
    wire [7:0] reversed;
    wire [3:0] popcount;
    wire [15:0] probe = {4'b0, reversed, popcount};

    bit_manip dut (
        .clk      (clk),
        .rst_n    (rst_n),
        .in       (cnt[7:0]),
        .reversed (reversed),
        .popcount (popcount)
    );
""",
    5: """\
    // sel=5  dff_array  probe={8'b0, q[7:0]}
    wire [7:0] q;
    wire [15:0] probe = {8'b0, q};

    dff_array dut (
        .clk  (clk),
        .rst_n(rst_n),
        .en   (cnt[0]),
        .d    (cnt[8:1]),
        .q    (q)
    );
""",
    6: """\
    // sel=6  shift_reg  probe={8'b0, q[7:0]}
    wire [7:0] q;
    wire [15:0] probe = {8'b0, q};

    shift_reg dut (
        .clk  (clk),
        .rst_n(rst_n),
        .en   (1'b1),
        .sin  (cnt[0]),
        .q    (q)
    );
""",
}


def make_testbench(sel_id: int) -> str:
    return _TB_HEADER + _DUT_BLOCKS[sel_id] + _TB_FOOTER


def extract_module_name(verilog_path: str) -> str:
    """Return the first module name found in the file."""
    with open(verilog_path) as f:
        src = f.read()
    m = re.search(r'\bmodule\s+(\w+)', src)
    if not m:
        raise ValueError(f"No module declaration found in {verilog_path}")
    return m.group(1)


def simulate(verilog_path: str, sel_id: int, work_dir: str) -> list[int]:
    """
    Compile candidate + testbench with iverilog, run vvp, parse output.
    Returns list of N_CYCLES integer probe values.
    Raises RuntimeError on compile or sim failure.
    """
    tb_path  = os.path.join(work_dir, "tb.v")
    out_path = os.path.join(work_dir, "sim.out")

    tb_src = make_testbench(sel_id)
    with open(tb_path, "w") as f:
        f.write(tb_src)

    # compile
    compile_cmd = [
        IVERILOG, "-g2012",
        "-o", out_path,
        verilog_path,
        tb_path,
    ]
    cp = subprocess.run(compile_cmd, capture_output=True, text=True)
    if cp.returncode != 0:
        raise RuntimeError(f"COMPILE_FAIL\n{cp.stderr.strip()}")

    # simulate
    run_cmd = ["vvp", out_path]
    rp = subprocess.run(run_cmd, capture_output=True, text=True, timeout=120)
    if rp.returncode != 0:
        raise RuntimeError(f"SIM_FAIL\n{rp.stderr.strip()}")

    # parse "$display("%0d %0d", cycle, probe)" lines
    samples = []
    for line in rp.stdout.splitlines():
        parts = line.split()
        if len(parts) == 2:
            try:
                samples.append(int(parts[1]))
            except ValueError:
                pass

    if len(samples) < N_CYCLES:
        raise RuntimeError(
            f"SIM_SHORT: got {len(samples)} samples, expected {N_CYCLES}"
        )

    return samples[:N_CYCLES]


def hamming_similarity(a: np.ndarray, b: np.ndarray, mask: int) -> float:
    """
    Normalized bit-level similarity over meaningful bits only (defined by mask).
    Returns fraction of masked bits that match (1.0 = identical).
    """
    a_m = a.astype(np.uint32) & mask
    b_m = b.astype(np.uint32) & mask
    xor = np.bitwise_xor(a_m, b_m)
    differing_bits = int(np.unpackbits(xor.view(np.uint8)).sum())
    # count bits set in mask = number of meaningful bits per sample
    meaningful_bits_per_sample = bin(mask).count('1')
    total_bits = len(a) * meaningful_bits_per_sample
    return 1.0 - differing_bits / total_bits


def score(verilog_path: str, sel_id: int) -> float:
    design_name = DESIGN_NAMES[sel_id]
    hw_waveform_path = os.path.join(RTL_LIB, design_name, "waveform.npy")

    if not os.path.exists(hw_waveform_path):
        raise FileNotFoundError(f"Hardware waveform not found: {hw_waveform_path}")

    hw = np.load(hw_waveform_path).astype(np.uint16)
    if len(hw) != N_CYCLES:
        raise ValueError(f"Hardware waveform has {len(hw)} samples, expected {N_CYCLES}")

    with tempfile.TemporaryDirectory() as work_dir:
        sim_samples = simulate(verilog_path, sel_id, work_dir)

    sim = np.array(sim_samples, dtype=np.uint16)
    return hamming_similarity(hw, sim, PROBE_MASKS[sel_id])


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <verilog_file> <sel_id>", file=sys.stderr)
        sys.exit(1)

    verilog_path = sys.argv[1]
    sel_id = int(sys.argv[2])

    if sel_id < 0 or sel_id > 6:
        print(f"sel_id must be 0-6, got {sel_id}", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(verilog_path):
        print(f"File not found: {verilog_path}", file=sys.stderr)
        sys.exit(1)

    try:
        reward = score(verilog_path, sel_id)
        print(f"{reward:.6f}")
    except RuntimeError as e:
        print(str(e), file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(3)


if __name__ == "__main__":
    main()
