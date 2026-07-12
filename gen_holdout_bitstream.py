#!/usr/bin/env python3
"""
gen_holdout_bitstream.py  -  Phase C step 2: the SILICON money-table bitstream.

Packs, into ONE reset-on-arm dut_top (same validated harness as the Phase-2
catalog flow: la_axi_fast + counter stimulus + echo canary), the head-to-head
silicon shootout on HELD-OUT designs:

  for each chosen held-out design:  the SFT policy's (count-weighted) MEDIAN
  candidate  vs  the GRPO policy's TOP candidate -- both drawn from the Phase-B
  held-out eval artifacts (rtl/holdout_eval: fmax_manifest.json + ppa.jsonl),
  i.e. real sampled RTL from each policy, already oracle-verified at seeds 1&2
  and Vivado-synthesized.

Designs (frozen pick, spans regimes/families, all high-GRPO-correctness):
  interp: fir26_8b, firr26, poly7_8b     extrap: firr36, poly8_v6_8b

Goldens are generated per design from the SAME coefficient derivations the
oracle uses (GAC), with the catalog counter stimulus x[c]=c&0xFF; both policies'
entries share the design's golden (they are I/O-equivalent implementations; the
sweep's two-sided shift absorbs latency differences).

    sandbox/server: python gen_holdout_bitstream.py      # + self-check via iverilog
    laptop        : "<vivado.bat>" -mode batch -source rtl/holdout_silicon/build_holdout.tcl
    board         : sudo -E /usr/local/share/pynq-venv/bin/python3 sweep_catalog.py \
                        --bit rtl/holdout_silicon/out/system_holdout.bit \
                        --sels rtl/holdout_silicon/holdout_sels.json \
                        --lo 30 --hi 340 --step 5 --runs 3
"""

import os
import json
import shutil
import argparse
from collections import defaultdict

import gen_accelerator_catalog as GAC

HERE = os.path.dirname(os.path.abspath(__file__))
EVAL_DIR = os.path.join(HERE, "rtl", "holdout_eval")
OUT_DIR = os.path.join(HERE, "rtl", "holdout_silicon")
LIB = os.path.join(HERE, "rtl_library")

# frozen design picks (see MASTER_REFERENCE Phase C): (design, regime, entry_stub)
PICKS = [
    ("fir26_8b",    "interp", "fir26"),
    ("firr26",      "interp", "firr26"),
    ("poly7_8b",    "interp", "poly7"),
    ("firr36",      "extrap", "firr36"),
    ("poly8_v6_8b", "extrap", "poly8v6"),
]


def golden_text(design):
    """golden.py content for a held-out design (counter stimulus, GAC coeffs)."""
    import re
    m = re.match(r"fir(\d+)_8b$", design)
    if m:
        return GAC.fir_golden(GAC.fir_coeffs(int(m.group(1))))
    m = re.match(r"firr(\d+)$", design)
    if m:
        T = int(m.group(1))
        return GAC.fir_golden([k + 1 for k in range(T)])
    m = re.match(r"poly(\d+)_v(\d+)_8b$", design)
    if m:
        return GAC.poly_golden(GAC.poly_coeffs_var(int(m.group(1)),
                                                   int(m.group(2))))
    m = re.match(r"poly(\d+)_8b$", design)
    if m:
        return GAC.poly_golden(GAC.poly_coeffs(int(m.group(1))))
    raise ValueError(design)


def load_eval():
    mani = json.load(open(os.path.join(EVAL_DIR, "fmax_manifest.json")))
    fmax = {}
    for line in open(os.path.join(EVAL_DIR, "ppa.jsonl")):
        try:
            p = json.loads(line)
        except ValueError:
            continue
        if p.get("compiled"):
            fmax[p["module"]] = float(p.get("fmax_mhz", 0.0))
    return mani, fmax


def pick_candidates(mani, fmax):
    """(policy, design) -> chosen module. GRPO = top real Fmax (count breaks
    ties); SFT = count-weighted MEDIAN real Fmax (the policy's typical output,
    per the frozen Phase-C plan)."""
    by = defaultdict(list)          # (policy, design) -> [(fmax, count, module)]
    for mod, info in mani.items():
        if mod not in fmax:
            continue
        by[(info["policy"], info["design"])].append(
            (fmax[mod], info["count"], mod))
    chosen = {}
    for (design, regime, stub) in PICKS:
        g = sorted(by[("grpo", design)], key=lambda t: (t[0], t[1]))
        s = by[("sft", design)]
        if not g or not s:
            raise SystemExit(f"missing candidates for {design} "
                             f"(grpo={len(g)}, sft={len(s)})")
        chosen[("grpo", design)] = g[-1][2]           # top Fmax
        expanded = sorted(f for f, c, _ in s for _ in range(c))
        med = expanded[len(expanded) // 2]            # count-weighted median
        s_pick = min(s, key=lambda t: (abs(t[0] - med), -t[1]))
        chosen[("sft", design)] = s_pick[2]
    return chosen


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="iverilog-verify every picked DUT against its golden "
                         "under the counter stimulus (needs iverilog+numpy)")
    args = ap.parse_args()

    mani, fmax = load_eval()
    chosen = pick_candidates(mani, fmax)

    duts_dir = os.path.join(OUT_DIR, "duts")
    os.makedirs(duts_dir, exist_ok=True)

    # sel map: GRPO/SFT pairs per design, canary last
    entries = []                                 # (sel, entry, module, role, file)
    sel = 0
    for design, regime, stub in PICKS:
        for pol in ("sft", "grpo"):
            mod = chosen[(pol, design)]
            src = os.path.join(EVAL_DIR, mod + ".sv")
            dst = os.path.join(duts_dir, mod + ".v")
            shutil.copyfile(src, dst)
            entry = f"{pol}_{stub}"
            entries.append((sel, entry, mod, "dut", dst))
            # golden: same design reference for both policies
            gd = os.path.join(LIB, entry)
            os.makedirs(gd, exist_ok=True)
            open(os.path.join(gd, "golden.py"), "w").write(golden_text(design))
            sel += 1
    entries.append((sel, "echo8b", "echo8b", "canary",
                    os.path.join(LIB, "echo8b", "design.v")))

    print("sel map (design pairs, sft median vs grpo top, real Vivado MHz):")
    for s, entry, mod, role, _ in entries:
        f = fmax.get(mod)
        print(f"  sel {s:2d}: {entry:12s} -> {mod:26s} "
              f"{'' if f is None else f'{f:6.1f} MHz'} ({role})")

    # ---- dut_top ----
    wires = "\n".join(f"    wire [15:0] y{s};" for s, *_ in entries)
    insts = "\n".join(
        f"    {mod} u{s} ( .clk(clk), .rst_n(dut_rst_n), "
        f".x(cnt[7:0]), .y(y{s}) );" for s, _, mod, _, _ in entries)
    cases = "\n".join(f"            6'd{s}: probe = y{s};"
                      for s, *_ in entries)
    dut_top = f"""`timescale 1ns/1ps
// Auto-generated by gen_holdout_bitstream.py - Phase C silicon money table.
// Reset-on-arm: stimulus counter + all DUTs held in reset until `cap`.
module dut_top (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        cap,
    input  wire [5:0]  sel,
    output reg  [15:0] probe
);
    wire dut_rst_n = rst_n & cap;
    reg [31:0] cnt;
    always @(posedge clk)
        if (!rst_n || !cap) cnt <= 32'b0;
        else                cnt <= cnt + 1'b1;

{wires}

{insts}

    always @(*) begin
        case (sel)
{cases}
            default: probe = 16'b0;
        endcase
    end
endmodule
"""
    open(os.path.join(OUT_DIR, "dut_top_holdout.v"), "w").write(dut_top)

    # ---- build tcl (same validated BD as the catalog flow) ----
    dut_files = " \\\n    ".join(
        f"[file join $ROOT rtl holdout_silicon duts {os.path.basename(p)}]"
        for *_x, role, p in entries if role == "dut")
    build_tcl = f"""# Auto-generated - Phase C held-out silicon money-table bitstream.
set PART    "xc7z020clg400-1"
set CLK_MHZ 200
set ROOT    [file normalize [file join [file dirname [info script]] .. ..]]
set OUT     [file join $ROOT rtl holdout_silicon out]
file mkdir $OUT

create_project sys_holdout [file join $OUT proj] -part $PART -force
add_files [list \\
    [file join $ROOT rtl la_axi_fast.v] \\
    [file join $ROOT rtl holdout_silicon dut_top_holdout.v] \\
    [file join $ROOT rtl_library echo8b design.v] \\
    {dut_files} ]
update_compile_order -fileset sources_1

create_bd_design "system"
create_bd_cell -type ip -vlnv xilinx.com:ip:processing_system7:5.5 ps7
apply_bd_automation -rule xilinx.com:bd_rule:processing_system7 \\
    -config {{make_external "FIXED_IO, DDR" apply_board_preset "1"}} \\
    [get_bd_cells ps7]
set_property -dict [list CONFIG.PCW_FPGA0_PERIPHERAL_FREQMHZ $CLK_MHZ] \\
    [get_bd_cells ps7]
create_bd_cell -type module -reference la_axi_fast la0
create_bd_cell -type module -reference dut_top      dut0
apply_bd_automation -rule xilinx.com:bd_rule:axi4 \\
    -config {{Master "/ps7/M_AXI_GP0" Clk "Auto"}} \\
    [get_bd_intf_pins la0/S_AXI]
connect_bd_net [get_bd_pins la0/sel]       [get_bd_pins dut0/sel]
connect_bd_net [get_bd_pins la0/probe]     [get_bd_pins dut0/probe]
connect_bd_net [get_bd_pins la0/capturing] [get_bd_pins dut0/cap]
connect_bd_net [get_bd_pins dut0/clk]   [get_bd_pins la0/S_AXI_ACLK]
connect_bd_net [get_bd_pins dut0/rst_n] [get_bd_pins la0/S_AXI_ARESETN]
assign_bd_address
validate_bd_design
save_bd_design

make_wrapper -files [get_files system.bd] -top -force
add_files -norecurse [glob \\
    [file join $OUT proj *.gen sources_1 bd system hdl system_wrapper.v] \\
    [file join $OUT proj *.srcs sources_1 bd system hdl system_wrapper.v]]
set_property top system_wrapper [current_fileset]

launch_runs synth_1 -jobs 8
wait_on_run synth_1
launch_runs impl_1 -to_step write_bitstream -jobs 8
wait_on_run impl_1
file copy -force [glob [file join $OUT proj *.runs impl_1 system_wrapper.bit]] \\
    [file join $OUT system_holdout.bit]
set hwh [glob -nocomplain \\
    [file join $OUT proj *.gen sources_1 bd system hw_handoff system.hwh] \\
    [file join $OUT proj *.srcs sources_1 bd system hw_handoff system.hwh]]
if {{$hwh ne ""}} {{
    file copy -force [lindex $hwh 0] [file join $OUT system_holdout.hwh]
}}
puts "HOLDOUT BITSTREAM DONE"
"""
    open(os.path.join(OUT_DIR, "build_holdout.tcl"), "w").write(build_tcl)

    sels = {entry: {"sel": s, "role": role, "module": mod}
            for s, entry, mod, role, _ in entries}
    json.dump(sels, open(os.path.join(OUT_DIR, "holdout_sels.json"), "w"),
              indent=1)
    print(f"\nwrote {OUT_DIR}/{{dut_top_holdout.v, build_holdout.tcl, "
          f"holdout_sels.json, duts/*.v}} + rtl_library/<entry>/golden.py x10")

    if args.check:
        self_check(entries)

    print("\nnext: laptop  vivado -mode batch -source "
          "rtl/holdout_silicon/build_holdout.tcl\n"
          "then board    sweep_catalog.py --bit rtl/holdout_silicon/out/"
          "system_holdout.bit --sels rtl/holdout_silicon/holdout_sels.json "
          "--lo 30 --hi 340 --step 5 --runs 3")


def self_check(entries, n=1200):
    """iverilog: drive each picked DUT with the COUNTER stimulus and require
    >=0.999 match vs its generated golden (two-sided shift <=8) -- proves the
    golden/DUT pairing before any Vivado time is spent."""
    import numpy as np
    import importlib.util
    import oracle

    stim = (np.arange(n) & 0xFF).astype(np.uint16)
    print("\nself-check (counter stimulus vs generated goldens):")
    bad = 0
    for s, entry, mod, role, path in entries:
        gp = os.path.join(LIB, entry, "golden.py")
        spec = importlib.util.spec_from_file_location("g_" + entry, gp)
        gmod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gmod)
        golden = gmod.compute_golden(n).astype(np.uint16)
        y = oracle.run_dut(open(path).read(), mod, stim, 8)
        if y is None:
            print(f"  {entry:12s} ** SIM FAIL **"); bad += 1; continue
        best = 0.0
        for sh in range(9):
            for a, b in ((y[8:], golden[sh:]), (y[8 + sh:], golden)):
                k = min(len(a), len(b), 1024)
                if k >= 64:
                    best = max(best, float(np.mean(a[:k] == b[:k])))
        ok = best >= 0.999
        bad += (not ok)
        print(f"  {entry:12s} match={best:.4f} {'OK' if ok else '** MISMATCH **'}")
    if bad:
        raise SystemExit(f"{bad} self-check failures -- DO NOT build the bitstream")
    print("all DUT/golden pairings verified -- safe to build")


if __name__ == "__main__":
    main()
