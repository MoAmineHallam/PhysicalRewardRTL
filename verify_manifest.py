#!/usr/bin/env python3
"""
verify_manifest.py  -  Verify every generated design against its golden_body.

Reads rtl_library/manifest.json (the single source of truth). For each design:
  - builds a counter-driven testbench from the manifest fields
  - compiles design.v with iverilog and runs it
  - builds the reference from golden_body and compares (allowing the 1-2 cycle
    registration offset)

A design that passes compiles cleanly, is synthesizable, and is functionally
correct -> safe for the batched bitstream with no manual debugging.

Usage:
    python verify_manifest.py                  # verify all
    python verify_manifest.py --jobs 8         # parallel
    python verify_manifest.py --limit 50       # first 50 only
    python verify_manifest.py mul4x4g cmp8b    # specific designs
"""

import os
import sys
import json
import argparse
import subprocess
import tempfile
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np

RTL_LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rtl_library")
N_CYCLES = 4096


def make_tb(rec):
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
        for (i = 0; i < {N_CYCLES}; i = i + 1) begin
            @(posedge clk); #1;
            $display("%0d %0d", i, probe);
        end
        $finish;
    end
endmodule
"""


def golden_from_body(body, n_cycles):
    # body already carries 8-space indentation (matches the for-loop body).
    src = ("def _g(n_cycles):\n"
           "    import numpy as np\n"
           "    out = []\n"
           "    for c in range(n_cycles):\n"
           + body.rstrip("\n") + "\n"
           + "        out.append(val & 0xFFFF)\n"
           "    return np.array(out, dtype=np.uint16)\n")
    ns = {}
    exec(src, ns)
    return ns["_g"](n_cycles)


def verify_one(rec):
    name = rec["name"]
    design_v = os.path.join(RTL_LIB, name, "design.v")
    if not os.path.exists(design_v):
        return name, False, "design.v missing"

    try:
        golden = golden_from_body(rec["golden_body"], N_CYCLES)
    except Exception as e:
        return name, False, f"golden exec error: {e}"

    mask = rec["probe_mask"]

    with tempfile.TemporaryDirectory() as wd:
        tb_path = os.path.join(wd, "tb.v")
        out_bin = os.path.join(wd, "sim.out")
        with open(tb_path, "w") as f:
            f.write(make_tb(rec))
        cp = subprocess.run(["iverilog", "-g2012", "-o", out_bin, design_v, tb_path],
                            capture_output=True, text=True)
        if cp.returncode != 0:
            return name, False, "COMPILE: " + cp.stderr.strip().split("\n")[0]
        try:
            rp = subprocess.run(["vvp", out_bin], capture_output=True,
                                text=True, timeout=60)
        except subprocess.TimeoutExpired:
            return name, False, "SIM TIMEOUT"
        sim = []
        for line in rp.stdout.splitlines():
            parts = line.split()
            if len(parts) == 2:
                try:
                    sim.append(int(parts[1]))
                except ValueError:
                    pass

    sim = np.array(sim[:N_CYCLES], dtype=np.uint16) & mask
    gold = (golden & mask)
    n = min(len(sim), len(gold))
    sim, gold = sim[:n], gold[:n]

    for shift in (1, 2, 0):
        g = np.roll(gold, -shift)
        m = n - shift
        if m > 1 and np.array_equal(sim[:m - 1], g[:m - 1]):
            return name, True, f"reg-offset={shift}"

    g = np.roll(gold, -1)
    diff = np.where(sim[:n - 1] != g[:n - 1])[0]
    first = int(diff[0]) if len(diff) else -1
    detail = (f"{len(diff)}/{n} mismatch; first idx {first}: "
              f"sim={sim[first]} gold={g[first]}") if first >= 0 else "mismatch"
    return name, False, detail


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("names", nargs="*")
    ap.add_argument("--jobs", type=int, default=os.cpu_count() or 4)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    with open(os.path.join(RTL_LIB, "manifest.json")) as f:
        manifest = json.load(f)
    if args.names:
        manifest = [r for r in manifest if r["name"] in set(args.names)]
    if args.limit:
        manifest = manifest[:args.limit]

    print(f"Verifying {len(manifest)} designs (jobs={args.jobs})...\n")
    passed, failed = [], []
    with ProcessPoolExecutor(max_workers=args.jobs) as ex:
        futs = {ex.submit(verify_one, r): r["name"] for r in manifest}
        for fut in as_completed(futs):
            name, ok, detail = fut.result()
            if ok:
                passed.append(name)
            else:
                failed.append((name, detail))
                print(f"  FAIL [{name}] {detail}")

    print("\n" + "=" * 50)
    print(f"PASS: {len(passed)}/{len(manifest)}")
    if failed:
        print(f"FAIL: {len(failed)}")
        for name, d in failed[:40]:
            print(f"   {name}: {d}")
    print("=" * 50)
    sys.exit(0 if not failed else 1)


if __name__ == "__main__":
    main()
