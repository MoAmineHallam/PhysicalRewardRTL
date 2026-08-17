#!/usr/bin/env python3
"""Build inputs for a symmetric held-out PYNQ-Z2 comparison.

This is deliberately separate from ``gen_holdout_bitstream.py``.  The legacy
generator selected a count-weighted SFT median but the highest-Fmax GRPO
candidate.  This generator applies one rule to both policies:

  * consider candidates that have a successful real-Vivado row;
  * weight each unique candidate by its sample count in ``fmax_manifest.json``;
  * select the upper count-weighted median Fmax candidate;
  * if several modules have that exact median Fmax, prefer the largest count,
    then the lexicographically smallest module name.

The historical five designs are retained so that only candidate selection
changes.  They remain a post-hoc design set and are not a randomized sample.
Every selected module is traced to one of the three 30-design v8 artifact
directories in ``selection_manifest.json``.

Typical use::

    python gen_symmetric_holdout_bitstream.py --check
    vivado -mode batch -source \
        rtl/holdout_silicon_symmetric/build_holdout_symmetric.tcl

Only a live board sweep may create ``catalog_fmax.json``; this generator never
creates that file.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

import gen_holdout_bitstream as legacy


ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "rtl" / "holdout_silicon_symmetric"
LIB_DIR = ROOT / "rtl_library"
EVAL_DIRS = (
    ROOT / "rtl" / "holdout_eval_v8_firfirr",
    ROOT / "rtl" / "holdout_eval_v8_iirmed",
    ROOT / "rtl" / "holdout_eval_v8_poly",
)

# Keep the historical post-hoc design set fixed.  This removes the policy-side
# candidate-selection asymmetry, but does not turn design selection into a
# preregistered or random sample.
PICKS = tuple(legacy.PICKS)
POLICIES = ("sft", "grpo")
SELECTION_RULE = "upper_count_weighted_median_real_vivado_fmax"
SELECTION_RULE_DETAIL = (
    "For each policy/design, retain manifest candidates with count > 0 and "
    "one compiled ppa.jsonl row. Aggregate sample count at each exact "
    "fmax_mhz, choose the first Fmax whose cumulative weight exceeds "
    "floor(total_compiled_weight/2), then break exact-Fmax module ties by "
    "larger count and lexicographically smaller module name."
)


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def git_head() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def load_artifacts():
    """Load the three v8 artifact directories with strict provenance."""
    manifest_rows = {}
    ppa_rows = {}
    source_files = []

    for eval_dir in EVAL_DIRS:
        manifest_path = eval_dir / "fmax_manifest.json"
        ppa_path = eval_dir / "ppa.jsonl"
        if not manifest_path.is_file() or not ppa_path.is_file():
            raise SystemExit(f"missing v8 artifact(s) in {rel(eval_dir)}")

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(manifest, dict):
            raise SystemExit(f"expected JSON object in {rel(manifest_path)}")

        for module, info in manifest.items():
            if module in manifest_rows:
                raise SystemExit(f"duplicate manifest module across v8 dirs: {module}")
            manifest_rows[module] = {
                "info": info,
                "manifest_path": manifest_path,
                "manifest_pointer": f"/{module}",
                "eval_dir": eval_dir,
            }

        with ppa_path.open(encoding="utf-8") as stream:
            for line_number, line in enumerate(stream, 1):
                try:
                    row = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise SystemExit(
                        f"invalid JSON at {rel(ppa_path)}:{line_number}: {exc}"
                    ) from exc
                module = row.get("module")
                if not module or not row.get("compiled"):
                    continue
                if module in ppa_rows:
                    previous = ppa_rows[module]
                    raise SystemExit(
                        "duplicate compiled PPA row for "
                        f"{module}: {previous['ppa_path']}:{previous['line_number']} "
                        f"and {rel(ppa_path)}:{line_number}"
                    )
                try:
                    fmax_mhz = float(row["fmax_mhz"])
                except (KeyError, TypeError, ValueError) as exc:
                    raise SystemExit(
                        f"invalid fmax_mhz at {rel(ppa_path)}:{line_number}"
                    ) from exc
                if fmax_mhz <= 0.0:
                    raise SystemExit(
                        f"non-positive fmax_mhz at {rel(ppa_path)}:{line_number}"
                    )
                ppa_rows[module] = {
                    "row": row,
                    "fmax_mhz": fmax_mhz,
                    "ppa_path": rel(ppa_path),
                    "line_number": line_number,
                }

        source_files.append(
            {
                "eval_dir": rel(eval_dir),
                "fmax_manifest": rel(manifest_path),
                "fmax_manifest_sha256": sha256(manifest_path),
                "ppa_jsonl": rel(ppa_path),
                "ppa_jsonl_sha256": sha256(ppa_path),
            }
        )

    return manifest_rows, ppa_rows, source_files


def select_candidates(manifest_rows, ppa_rows):
    by_pair = defaultdict(list)
    all_by_pair = defaultdict(list)
    wanted = {(policy, design) for design, _regime, _stub in PICKS for policy in POLICIES}

    for module, source in manifest_rows.items():
        info = source["info"]
        pair = (info.get("policy"), info.get("design"))
        if pair not in wanted:
            continue
        try:
            count = int(info["count"])
        except (KeyError, TypeError, ValueError) as exc:
            raise SystemExit(f"invalid count at {source['manifest_pointer']}") from exc
        if count <= 0:
            raise SystemExit(f"non-positive count for manifest module {module}")
        candidate = {
            "module": module,
            "count": count,
            "source": source,
            "ppa": ppa_rows.get(module),
        }
        all_by_pair[pair].append(candidate)
        if candidate["ppa"] is not None:
            by_pair[pair].append(candidate)

    selected = {}
    population = {}
    for design, expected_regime, _stub in PICKS:
        for policy in POLICIES:
            pair = (policy, design)
            all_candidates = all_by_pair[pair]
            candidates = by_pair[pair]
            if not all_candidates or not candidates:
                raise SystemExit(
                    f"missing candidates for {policy}/{design}: "
                    f"manifest={len(all_candidates)}, compiled={len(candidates)}"
                )
            regimes = {c["source"]["info"].get("regime") for c in all_candidates}
            if regimes != {expected_regime}:
                raise SystemExit(
                    f"regime mismatch for {policy}/{design}: {sorted(regimes)}"
                )

            weight_by_fmax = defaultdict(int)
            for candidate in candidates:
                weight_by_fmax[candidate["ppa"]["fmax_mhz"]] += candidate["count"]
            compiled_weight = sum(c["count"] for c in candidates)
            rank_zero_based = compiled_weight // 2  # upper median, as legacy used
            cumulative = 0
            median_fmax = None
            for fmax_mhz in sorted(weight_by_fmax):
                cumulative += weight_by_fmax[fmax_mhz]
                if cumulative > rank_zero_based:
                    median_fmax = fmax_mhz
                    break
            assert median_fmax is not None

            tied = [c for c in candidates if c["ppa"]["fmax_mhz"] == median_fmax]
            chosen = sorted(tied, key=lambda c: (-c["count"], c["module"]))[0]
            selected[pair] = chosen
            population[pair] = {
                "manifest_unique_candidates": len(all_candidates),
                "manifest_sample_weight": sum(c["count"] for c in all_candidates),
                "vivado_compiled_unique_candidates": len(candidates),
                "vivado_compiled_sample_weight": compiled_weight,
                "excluded_noncompiled_unique_candidates": len(all_candidates) - len(candidates),
                "excluded_noncompiled_sample_weight": (
                    sum(c["count"] for c in all_candidates) - compiled_weight
                ),
                "upper_median_rank_zero_based": rank_zero_based,
                "median_fmax_mhz": median_fmax,
                "exact_fmax_tie_modules": sorted(c["module"] for c in tied),
            }

    return selected, population


def verify_golden(entry: str, design: str) -> Path:
    golden_path = LIB_DIR / entry / "golden.py"
    if not golden_path.is_file():
        raise SystemExit(f"missing tracked golden: {rel(golden_path)}")
    expected = legacy.golden_text(design)
    actual = golden_path.read_text(encoding="utf-8")
    if actual != expected:
        raise SystemExit(
            f"golden provenance mismatch for {entry}: {rel(golden_path)} "
            "does not equal the current design-derived reference"
        )
    return golden_path


def write_generated(selected, population, source_files):
    duts_dir = OUT_DIR / "duts"
    duts_dir.mkdir(parents=True, exist_ok=True)

    entries = []
    manifest_selections = []
    expected_dut_names = set()
    sel = 0
    for design, regime, stub in PICKS:
        for policy in POLICIES:
            candidate = selected[(policy, design)]
            module = candidate["module"]
            source = candidate["source"]
            ppa = candidate["ppa"]
            src = source["eval_dir"] / f"{module}.sv"
            if not src.is_file():
                raise SystemExit(f"selected RTL does not exist: {rel(src)}")
            dst = duts_dir / f"{module}.v"
            shutil.copyfile(src, dst)
            expected_dut_names.add(dst.name)

            entry = f"{policy}_{stub}"
            golden_path = verify_golden(entry, design)
            entries.append((sel, entry, module, "dut", dst))
            manifest_selections.append(
                {
                    "sel": sel,
                    "entry": entry,
                    "role": "dut",
                    "policy": policy,
                    "design": design,
                    "regime": regime,
                    "selection_rule": SELECTION_RULE,
                    "module": module,
                    "sample_count": candidate["count"],
                    "real_vivado_fmax_mhz": ppa["fmax_mhz"],
                    "population": population[(policy, design)],
                    "provenance": {
                        "eval_dir": rel(source["eval_dir"]),
                        "manifest": rel(source["manifest_path"]),
                        "manifest_json_pointer": source["manifest_pointer"],
                        "ppa": ppa["ppa_path"],
                        "ppa_line": ppa["line_number"],
                        "rtl": rel(src),
                        "rtl_sha256": sha256(src),
                        "copied_rtl": rel(dst),
                        "copied_rtl_sha256": sha256(dst),
                        "golden": rel(golden_path),
                        "golden_sha256": sha256(golden_path),
                    },
                }
            )
            sel += 1

    stale_duts = sorted(
        path.name for path in duts_dir.glob("*.v") if path.name not in expected_dut_names
    )
    if stale_duts:
        raise SystemExit(
            "refusing ambiguous output directory with stale DUTs: " + ", ".join(stale_duts)
        )

    canary_path = LIB_DIR / "echo8b" / "design.v"
    canary_golden = LIB_DIR / "echo8b" / "golden.py"
    entries.append((sel, "echo8b", "echo8b", "canary", canary_path))

    wires = "\n".join(f"    wire [15:0] y{s};" for s, *_ in entries)
    insts = "\n".join(
        f"    {module} u{s} ( .clk(clk), .rst_n(dut_rst_n), "
        f".x(cnt[7:0]), .y(y{s}) );"
        for s, _entry, module, _role, _path in entries
    )
    cases = "\n".join(f"            6'd{s}: probe = y{s};" for s, *_ in entries)
    dut_top = f"""`timescale 1ns/1ps
// Generated by gen_symmetric_holdout_bitstream.py.
// Both policies use the same count-weighted median real-Vivado selection rule.
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
    (OUT_DIR / "dut_top_holdout.v").write_text(dut_top, encoding="utf-8", newline="\n")

    dut_files = " \\\n    ".join(
        f"[file join $ROOT rtl holdout_silicon_symmetric duts {path.name}]"
        for _s, _entry, _module, role, path in entries
        if role == "dut"
    )
    build_tcl = f"""# Generated symmetric held-out comparison bitstream.
set PART    "xc7z020clg400-1"
set CLK_MHZ 200
set ROOT    [file normalize [file join [file dirname [info script]] .. ..]]
set OUT     [file join $ROOT rtl holdout_silicon_symmetric out]
file mkdir $OUT

create_project sys_holdout_symmetric [file join $OUT proj] -part $PART -force
add_files [list \\
    [file join $ROOT rtl la_axi_fast.v] \\
    [file join $ROOT rtl holdout_silicon_symmetric dut_top_holdout.v] \\
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

set_property synth_checkpoint_mode None [get_files system.bd]
generate_target all [get_files system.bd]
make_wrapper -files [get_files system.bd] -top -force
add_files -norecurse [glob \\
    [file join $OUT proj *.gen sources_1 bd system hdl system_wrapper.v] \\
    [file join $OUT proj *.srcs sources_1 bd system hdl system_wrapper.v]]
set_property top system_wrapper [current_fileset]

# Run in this Vivado process. The Windows run-manager launcher uses WSH child
# processes, which can stall in managed sessions before synthesis starts.
synth_design -top system_wrapper -part $PART -flatten_hierarchy rebuilt
write_checkpoint -force [file join $OUT post_synth.dcp]
report_utilization -file [file join $OUT utilization_post_synth.rpt]
opt_design
place_design
phys_opt_design
route_design
write_checkpoint -force [file join $OUT post_route.dcp]
report_route_status -file [file join $OUT route_status.rpt]
report_timing_summary -delay_type max -max_paths 20 \\
    -file [file join $OUT timing_summary_routed.rpt]
report_utilization -file [file join $OUT utilization_routed.rpt]
set worst_path [get_timing_paths -delay_type max -max_paths 1]
if {{$worst_path eq ""}} {{ error "no routed max-delay timing path found" }}
puts [format "SYMMETRIC HOLDOUT ROUTED WNS %.3f ns" \\
    [get_property SLACK $worst_path]]
write_bitstream -force [file join $OUT system_holdout_symmetric.bit]
set hwh [glob -nocomplain \\
    [file join $OUT proj *.gen sources_1 bd system hw_handoff system.hwh] \\
    [file join $OUT proj *.srcs sources_1 bd system hw_handoff system.hwh]]
if {{$hwh eq ""}} {{ error "system.hwh was not generated" }}
file copy -force [lindex $hwh 0] \\
    [file join $OUT system_holdout_symmetric.hwh]
puts "SYMMETRIC HOLDOUT BITSTREAM DONE"
"""
    (OUT_DIR / "build_holdout_symmetric.tcl").write_text(
        build_tcl, encoding="utf-8", newline="\n"
    )

    sels = {}
    for selection in manifest_selections:
        sels[selection["entry"]] = {
            "sel": selection["sel"],
            "role": "dut",
            "module": selection["module"],
            "policy": selection["policy"],
            "design": selection["design"],
            "regime": selection["regime"],
            "selection_rule": SELECTION_RULE,
            "real_vivado_fmax_mhz": selection["real_vivado_fmax_mhz"],
        }
    sels["echo8b"] = {
        "sel": sel,
        "role": "canary",
        "module": "echo8b",
        "provenance": {
            "rtl": rel(canary_path),
            "rtl_sha256": sha256(canary_path),
            "golden": rel(canary_golden),
            "golden_sha256": sha256(canary_golden),
        },
    }
    (OUT_DIR / "holdout_sels.json").write_text(
        json.dumps(sels, indent=2) + "\n", encoding="utf-8", newline="\n"
    )

    selection_manifest = {
        "schema_version": 1,
        "purpose": "symmetric policy-side PYNQ-Z2 held-out comparison",
        "git_head_at_generation": git_head(),
        "design_selection": {
            "rule": "historical_fixed_five_from_legacy_silicon_table",
            "is_preregistered_or_random": False,
            "warning": (
                "The five designs were historically selected post hoc with high GRPO "
                "correctness. Only policy-side candidate selection is symmetric."
            ),
            "designs": [
                {"design": design, "regime": regime, "entry_stub": stub}
                for design, regime, stub in PICKS
            ],
        },
        "candidate_selection": {
            "rule": SELECTION_RULE,
            "identical_for_policies": list(POLICIES),
            "detail": SELECTION_RULE_DETAIL,
            "conditioning": (
                "functional candidates represented in fmax_manifest.json that also "
                "have a successful real-Vivado ppa.jsonl row"
            ),
        },
        "board_measurement_plan": {
            "script": "sweep_catalog.py",
            "lo_mhz": 20.0,
            "hi_mhz": 260.0,
            "step_mhz": 5.0,
            "runs": 3,
            "depth": 2048,
            "n_score": 1024,
            "max_shift": 8,
            "similarity_threshold": 0.99,
            "canary_margin_mhz": 20.0,
            "primary_pairing": "within-design SFT median versus GRPO median",
            "result_rule": (
                "Do not create or report catalog_fmax.json unless the live board "
                "sweep completes and sweep_catalog.py writes the artifact."
            ),
        },
        "source_artifacts": source_files,
        "selections": manifest_selections,
        "canary": sels["echo8b"],
        "generated_outputs": {
            "dut_top": "rtl/holdout_silicon_symmetric/dut_top_holdout.v",
            "build_tcl": "rtl/holdout_silicon_symmetric/build_holdout_symmetric.tcl",
            "sels": "rtl/holdout_silicon_symmetric/holdout_sels.json",
            "bitstream_expected": (
                "rtl/holdout_silicon_symmetric/out/system_holdout_symmetric.bit"
            ),
            "hwh_expected": (
                "rtl/holdout_silicon_symmetric/out/system_holdout_symmetric.hwh"
            ),
            "board_result_reserved": (
                "rtl/holdout_silicon_symmetric/catalog_fmax.json"
            ),
        },
    }
    (OUT_DIR / "selection_manifest.json").write_text(
        json.dumps(selection_manifest, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return entries, manifest_selections


def self_check(entries, n=1200):
    """Verify every selected DUT without ``tempfile.TemporaryDirectory``.

    Some managed Windows workspaces deny writes inside Python's mode-0700
    temporary directories.  A generator-owned, mode-default work directory
    avoids turning that environment quirk into a false RTL failure while using
    the same vector-player testbench and trace parser as the project oracle.
    """
    import importlib.util

    import numpy as np
    import oracle

    work_dir = OUT_DIR / ".self_check_work"
    work_dir.mkdir(parents=True, exist_ok=True)
    stim = (np.arange(n) & 0xFF).astype(np.uint16)
    print("\nself-check (counter stimulus vs generated goldens):")
    bad = 0
    try:
        for _sel, entry, module, _role, rtl_path in entries:
            golden_path = LIB_DIR / entry / "golden.py"
            spec = importlib.util.spec_from_file_location("g_" + entry, golden_path)
            golden_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(golden_module)
            golden = golden_module.compute_golden(n).astype(np.uint16)

            candidate_path = work_dir / "cand.v"
            tb_path = work_dir / "tb.v"
            stim_path = work_dir / "stim.hex"
            vvp_path = work_dir / "a.vvp"
            candidate_path.write_text(
                Path(rtl_path).read_text(encoding="utf-8"), encoding="utf-8"
            )
            tb_path.write_text(oracle._tb(module, n, 8), encoding="utf-8")
            stim_path.write_text(
                "\n".join(f"{int(value):x}" for value in stim) + "\n",
                encoding="utf-8",
            )
            try:
                compiled = subprocess.run(
                    [
                        "iverilog",
                        "-g2012",
                        "-o",
                        str(vvp_path),
                        str(candidate_path),
                        str(tb_path),
                    ],
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                if compiled.returncode != 0:
                    print(
                        f"  {entry:12s} ** COMPILE FAIL ** "
                        f"{compiled.stderr.strip()}"
                    )
                    bad += 1
                    continue
                simulated = subprocess.run(
                    ["vvp", str(vvp_path)],
                    capture_output=True,
                    text=True,
                    cwd=work_dir,
                    timeout=60,
                )
            except FileNotFoundError as exc:
                raise SystemExit(
                    f"iverilog/vvp is unavailable ({exc}); self-check not performed"
                ) from exc
            except subprocess.TimeoutExpired:
                print(f"  {entry:12s} ** SIM TIMEOUT **")
                bad += 1
                continue

            y = oracle._parse_trace(simulated.stdout)
            if simulated.returncode != 0 or y is None or len(y) < 32:
                print(f"  {entry:12s} ** SIM FAIL **")
                bad += 1
                continue
            best = 0.0
            for shift in range(9):
                for actual, expected in (
                    (y[8:], golden[shift:]),
                    (y[8 + shift :], golden),
                ):
                    length = min(len(actual), len(expected), 1024)
                    if length >= 64:
                        best = max(
                            best,
                            float(np.mean(actual[:length] == expected[:length])),
                        )
            ok = best >= 0.999
            bad += int(not ok)
            print(f"  {entry:12s} match={best:.4f} {'OK' if ok else '** MISMATCH **'}")
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)

    if bad:
        raise SystemExit(f"{bad} self-check failures -- DO NOT build the bitstream")
    print("all DUT/golden pairings verified -- safe to build")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="iverilog-check all selected DUTs against their design-derived goldens",
    )
    args = parser.parse_args()

    manifest_rows, ppa_rows, source_files = load_artifacts()
    selected, population = select_candidates(manifest_rows, ppa_rows)
    entries, selections = write_generated(selected, population, source_files)

    print("symmetric sel map (weighted median real-Vivado candidate for both policies):")
    for selection in selections:
        print(
            f"  sel {selection['sel']:2d}: {selection['entry']:12s} -> "
            f"{selection['module']:28s} "
            f"{selection['real_vivado_fmax_mhz']:7.2f} MHz "
            f"(count={selection['sample_count']})"
        )
    print(f"  sel {entries[-1][0]:2d}: echo8b       -> echo8b (canary)")

    if args.check:
        self_check(entries)

    print(f"\nwrote {rel(OUT_DIR)}/selection_manifest.json and build inputs")
    print(
        "board results are intentionally absent until a live sweep writes "
        "rtl/holdout_silicon_symmetric/catalog_fmax.json"
    )
    print(
        "laptop: vivado -mode batch -source "
        "rtl/holdout_silicon_symmetric/build_holdout_symmetric.tcl"
    )
    print(
        "board: sudo -E /usr/local/share/pynq-venv/bin/python3 "
        "sweep_catalog.py --bit rtl/holdout_silicon_symmetric/out/"
        "system_holdout_symmetric.bit --sels rtl/holdout_silicon_symmetric/"
        "holdout_sels.json --lo 20 --hi 260 --step 5 --runs 3 --out "
        "rtl/holdout_silicon_symmetric/catalog_fmax.json"
    )


if __name__ == "__main__":
    main()
