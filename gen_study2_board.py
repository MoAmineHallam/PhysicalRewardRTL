#!/usr/bin/env python3
"""Generate the frozen, outcome-independent Study 2 PYNQ-Z2 board inputs.

Design and candidate selection are fixed in ``study2_board_spec.json``.  The
generator never reads reward, Fmax, area, or power while choosing a design or
RTL candidate.  It verifies the chosen candidates against the already-complete
PPA audit only after selection; a failure stops rather than reselecting.

Only a live PYNQ sweep may create ``rtl/sealed_study2_board/catalog_fmax.json``.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import importlib.util
import json
import pathlib
import shutil
import subprocess
from typing import Any

import numpy as np

import gen_accelerator_catalog as catalog
import oracle


ROOT = pathlib.Path(__file__).resolve().parent
SPEC_PATH = ROOT / "study2_board_spec.json"
AMENDMENT_PATH = ROOT / "study2_board_protocol_amendment.json"
SEALED_PATH = ROOT / "sealed_split.json"
PPA_AUDIT_PATH = ROOT / "sealed_ppa_audit_study2.json"
OUT = ROOT / "rtl" / "sealed_study2_board"
RESULT_PATH = OUT / "catalog_fmax.json"
ARMS = collections.OrderedDict(
    (
        ("sft", (ROOT / "rtl" / "sealed_sft",)),
        ("rf", (ROOT / "rtl" / "sealed_rf_s1", ROOT / "rtl" / "sealed_rf_s2")),
    )
)
FAMILIES = ("fir", "firr", "poly", "iir", "med")


class BoardInputError(RuntimeError):
    pass


def rel(path: pathlib.Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_lf(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def read_json(path: pathlib.Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise BoardInputError(f"cannot read valid JSON {rel(path)}: {exc}") from exc


def git_head() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def verify_spec(spec: dict) -> None:
    if spec.get("schema") != "study2_board_spec/1":
        raise BoardInputError("unexpected board specification schema")
    for name, expected in spec.get("inputs_sha256_lf", {}).items():
        path = ROOT / name
        if not path.is_file() or sha256_lf(path) != expected:
            raise BoardInputError(f"frozen board input mismatch: {name}")
    if spec.get("primary_outcome_unchanged") != "full_two_regime_repair":
        raise BoardInputError("board specification changed the primary outcome")
    design = spec.get("design_selection", {})
    if spec.get("amendment_record") != rel(AMENDMENT_PATH):
        raise BoardInputError("missing frozen board protocol amendment record")
    amendment = read_json(AMENDMENT_PATH)
    if amendment.get("schema") != "study2_board_protocol_amendment/1":
        raise BoardInputError("unexpected board amendment schema")
    if design.get("uses_policy_or_ppa_outcomes") is not True:
        raise BoardInputError("amended correctness eligibility is not disclosed")
    if design.get("outcome_use_limited_to") != "binary correctness eligibility only":
        raise BoardInputError("amended design eligibility is not bounded to correctness")
    if design.get("uses_reward_fmax_resource_or_power") is not False:
        raise BoardInputError("design selection uses a forbidden optimization outcome")
    candidate = spec.get("candidate_selection", {})
    if candidate.get("uses_reward_fmax_or_resource_values") is not False:
        raise BoardInputError("candidate selection uses forbidden outcome fields")
    if candidate.get("identical_for_arms") is not True:
        raise BoardInputError("candidate selection is not identical for both arms")


def load_arm_stats(sealed: dict) -> tuple[dict, list[dict]]:
    universe = {row["design"] for row in sealed.get("designs", [])}
    stats = {
        arm: {design: {"n": 0, "n_correct": 0} for design in universe}
        for arm in ARMS
    }
    sources = []
    for arm, directories in ARMS.items():
        for directory in directories:
            config_path = directory / "generation_config.json"
            summary_path = directory / "holdout_summary.json"
            config = read_json(config_path)
            summary = read_json(summary_path)
            policy = config.get("policy")
            rows = summary.get(policy)
            if not isinstance(rows, dict) or set(rows) != universe:
                raise BoardInputError(f"invalid design universe in {rel(summary_path)}")
            n_per_design = int(config.get("n_per_design", 0))
            for design in universe:
                row = rows[design]
                n = int(row.get("n", -1))
                n_correct = int(row.get("n_correct", -1))
                if n != n_per_design or not 0 <= n_correct <= n:
                    raise BoardInputError(f"invalid counts for {design} in {rel(summary_path)}")
                stats[arm][design]["n"] += n
                stats[arm][design]["n_correct"] += n_correct
            sources.append(
                {
                    "arm": arm,
                    "directory": rel(directory),
                    "generation_config": rel(config_path),
                    "generation_config_sha256": sha256(config_path),
                    "holdout_summary": rel(summary_path),
                    "holdout_summary_sha256": sha256(summary_path),
                }
            )
    return stats, sources


def select_designs(spec: dict, sealed: dict, arm_stats: dict) -> list[dict]:
    rows = sealed.get("designs")
    if not isinstance(rows, list) or len(rows) != 20:
        raise BoardInputError("sealed design universe is not exactly 20 rows")
    salt = spec["inputs_sha256_lf"]["sealed_split.json"]
    selected = []
    for family in FAMILIES:
        candidates = [
            row
            for row in rows
            if row.get("family") == family
            and arm_stats["sft"][row["design"]]["n_correct"] > 0
            and arm_stats["rf"][row["design"]]["n_correct"] > 0
        ]
        if not candidates:
            raise BoardInputError(f"sealed split has no correctness-eligible {family} design")
        ranked = sorted(
            candidates,
            key=lambda row: hashlib.sha256(
                f"{salt}:{family}:{row['design']}".encode("utf-8")
            ).hexdigest(),
        )
        chosen = dict(ranked[0])
        chosen["selection_digest"] = hashlib.sha256(
            f"{salt}:{family}:{chosen['design']}".encode("utf-8")
        ).hexdigest()
        chosen["correctness_eligibility"] = {
            arm: dict(arm_stats[arm][chosen["design"]]) for arm in ARMS
        }
        selected.append(chosen)
    if len(selected) != spec["design_selection"]["count"]:
        raise BoardInputError("design selection count differs from frozen specification")
    return selected


def load_compiled_rows() -> dict[str, dict]:
    audit = read_json(PPA_AUDIT_PATH)
    if audit.get("complete") is not True:
        raise BoardInputError("PPA audit is incomplete")
    rows = {}
    for directory in {path for dirs in ARMS.values() for path in dirs}:
        ppa_path = directory / "ppa.jsonl"
        for lineno, line in enumerate(ppa_path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            row = json.loads(line)
            module = row.get("module")
            if not isinstance(module, str) or module in rows:
                raise BoardInputError(f"duplicate or invalid PPA row: {module!r}")
            rows[module] = {
                "compiled": bool(row.get("compiled")),
                "fmax_mhz": row.get("fmax_mhz") if row.get("compiled") else None,
                "path": rel(ppa_path),
                "line": lineno,
            }
    return rows


def select_candidates(
    spec: dict,
    selected_designs: list[dict],
    arm_stats: dict,
    ppa_rows: dict[str, dict],
    sources: list[dict],
):
    wanted = {row["design"] for row in selected_designs}
    chosen = {}
    for arm, directories in ARMS.items():
        by_design_hash: dict[str, dict[str, dict]] = collections.defaultdict(
            lambda: collections.defaultdict(
                lambda: {"count": 0, "members": [], "emitted_hash": None}
            )
        )
        for directory in directories:
            manifest_path = directory / "fmax_manifest.json"
            manifest = read_json(manifest_path)
            if not isinstance(manifest, dict):
                raise BoardInputError(f"manifest is not an object: {rel(manifest_path)}")
            sources.append(
                {
                    "arm": arm,
                    "directory": rel(directory),
                    "manifest": rel(manifest_path),
                    "manifest_sha256": sha256(manifest_path),
                    "ppa": rel(directory / "ppa.jsonl"),
                    "ppa_sha256": sha256(directory / "ppa.jsonl"),
                }
            )
            manifest_counts: dict[str, int] = collections.Counter()
            for module, info in manifest.items():
                design = info.get("design")
                if design not in wanted:
                    continue
                count = int(info.get("count", 0))
                n = int(info.get("n", 0))
                emitted_hash = info.get("emitted_sha256")
                if count <= 0 or n <= 0 or not isinstance(emitted_hash, str):
                    raise BoardInputError(f"invalid candidate identity for {module}")
                manifest_counts[design] += count
                rtl_path = directory / f"{module}.sv"
                if not rtl_path.is_file():
                    raise BoardInputError(f"candidate RTL is missing: {rel(rtl_path)}")
                actual_emitted_hash = sha256(rtl_path)
                if actual_emitted_hash != emitted_hash:
                    raise BoardInputError(f"emitted RTL hash mismatch for {module}")
                group = by_design_hash[design][emitted_hash]
                group["count"] += count
                group["emitted_hash"] = emitted_hash
                group["members"].append(
                    {
                        "module": module,
                        "count": count,
                        "rtl": rtl_path,
                        "rtl_sha256": actual_emitted_hash,
                        "manifest": manifest_path,
                    }
                )
            config = read_json(directory / "generation_config.json")
            summary = read_json(directory / "holdout_summary.json")[config["policy"]]
            for design in wanted:
                if manifest_counts[design] != int(summary[design]["n_correct"]):
                    raise BoardInputError(
                        f"correct-candidate multiplicity mismatch for {design} in "
                        f"{rel(manifest_path)}"
                    )

        for design in wanted:
            groups = by_design_hash.get(design)
            total_n = arm_stats[arm][design]["n"]
            if not groups or total_n != spec["candidate_selection"]["samples_per_arm_design"]:
                raise BoardInputError(
                    f"{arm}/{design} does not have its frozen 48-sample arm budget"
                )
            winner = sorted(
                groups.values(), key=lambda group: (-group["count"], group["emitted_hash"])
            )[0]
            representative = sorted(
                winner["members"], key=lambda member: (member["module"], rel(member["rtl"]))
            )[0]
            ppa = ppa_rows.get(representative["module"])
            if not ppa or not ppa["compiled"]:
                raise BoardInputError(
                    f"post-selection PPA gate failed for {arm}/{design}/"
                    f"{representative['module']}; reselection is forbidden"
                )
            chosen[(arm, design)] = {
                "arm": arm,
                "design": design,
                "total_arm_samples": total_n,
                "total_arm_correct": arm_stats[arm][design]["n_correct"],
                "selected_rtl_occurrences": winner["count"],
                "selected_emitted_sha256": winner["emitted_hash"],
                "representative": representative,
                "identity_group_members": sorted(
                    (
                        {
                            "module": member["module"],
                            "count": member["count"],
                            "rtl": rel(member["rtl"]),
                            "rtl_sha256": member["rtl_sha256"],
                        }
                        for member in winner["members"]
                    ),
                    key=lambda row: (row["module"], row["rtl"]),
                ),
                "population_unique_rtl": len(groups),
                "post_selection_ppa_gate": ppa,
            }
    return chosen, sources


def golden_text(row: dict) -> str:
    family = row["family"]
    params = row["params"]
    if family in ("fir", "firr"):
        return catalog.fir_golden(params["coeffs"])
    if family == "poly":
        return catalog.poly_golden(params["coeffs"])
    if family == "iir":
        return catalog.iir_golden(params["coeffs"])
    if family == "med":
        return catalog.med_golden(params["window"])
    raise BoardInputError(f"no golden generator for family {family}")


def build_tcl(entries: list[dict]) -> str:
    dut_files = " \\\n    ".join(
        f"[file join $ROOT {rel(entry['copied_rtl']).replace('/', ' ')}]"
        for entry in entries if entry["role"] == "dut"
    )
    # The BD module-reference wrappers intentionally contain the referenced
    # module instantiation but Vivado 2023.1 can disable the original sources
    # before in-process top synthesis.  After BD generation, append the exact
    # referenced source closure to those generated wrappers and disable the
    # originals for synthesis.  This preserves one definition of every module.
    dut_sources = " \\\n    ".join(
        f"[file join $ROOT {rel(entry['copied_rtl']).replace('/', ' ')}]"
        for entry in entries if entry["role"] == "dut"
    )
    return f'''# Generated by gen_study2_board.py from study2_board_spec.json.
set PART "xc7z020clg400-1"
set CLK_MHZ 200
set ROOT [file normalize [file join [file dirname [info script]] .. ..]]
set OUT [file join $ROOT rtl sealed_study2_board out]
file mkdir $OUT

create_project sys_study2_board [file join $OUT proj] -part $PART -force
set original_sources [list \\
    [file join $ROOT rtl la_axi_fast.v] \\
    [file join $ROOT rtl sealed_study2_board dut_top.v] \\
    [file join $ROOT rtl_library echo8b design.v] \\
    {dut_files}]
add_files $original_sources
update_compile_order -fileset sources_1

create_bd_design "system"
create_bd_cell -type ip -vlnv xilinx.com:ip:processing_system7:5.5 ps7
apply_bd_automation -rule xilinx.com:bd_rule:processing_system7 \\
    -config {{make_external "FIXED_IO, DDR" apply_board_preset "1"}} \\
    [get_bd_cells ps7]
set_property -dict [list CONFIG.PCW_FPGA0_PERIPHERAL_FREQMHZ $CLK_MHZ] [get_bd_cells ps7]
create_bd_cell -type module -reference la_axi_fast la0
create_bd_cell -type module -reference dut_top dut0
apply_bd_automation -rule xilinx.com:bd_rule:axi4 \\
    -config {{Master "/ps7/M_AXI_GP0" Clk "Auto"}} [get_bd_intf_pins la0/S_AXI]
connect_bd_net [get_bd_pins la0/sel] [get_bd_pins dut0/sel]
connect_bd_net [get_bd_pins la0/probe] [get_bd_pins dut0/probe]
connect_bd_net [get_bd_pins la0/capturing] [get_bd_pins dut0/cap]
connect_bd_net [get_bd_pins dut0/clk] [get_bd_pins la0/S_AXI_ACLK]
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

proc append_source {{dst src}} {{
    set in [open $src r]
    set data [read $in]
    close $in
    set out [open $dst a]
    puts $out ""
    puts $out $data
    close $out
}}
set la_wrap [lindex [glob [file join $OUT proj *.gen sources_1 bd system ip system_la0_0 synth system_la0_0.v]] 0]
set dut_wrap [lindex [glob [file join $OUT proj *.gen sources_1 bd system ip system_dut0_0 synth system_dut0_0.v]] 0]
append_source $la_wrap [file join $ROOT rtl la_axi_fast.v]
append_source $dut_wrap [file join $ROOT rtl sealed_study2_board dut_top.v]
append_source $dut_wrap [file join $ROOT rtl_library echo8b design.v]
foreach src [list \\
    {dut_sources}] {{ append_source $dut_wrap $src }}
set_property used_in_synthesis false [get_files -of_objects [get_filesets sources_1] $original_sources]
set_property top system_wrapper [current_fileset]
update_compile_order -fileset sources_1

synth_design -top system_wrapper -part $PART -flatten_hierarchy rebuilt
write_checkpoint -force [file join $OUT post_synth.dcp]
report_utilization -file [file join $OUT utilization_post_synth.rpt]
opt_design
place_design
phys_opt_design
route_design
write_checkpoint -force [file join $OUT post_route.dcp]
report_route_status -file [file join $OUT route_status.rpt]
report_timing_summary -delay_type max -max_paths 20 -file [file join $OUT timing_summary_routed.rpt]
report_utilization -file [file join $OUT utilization_routed.rpt]
set worst_path [get_timing_paths -delay_type max -max_paths 1]
if {{$worst_path eq ""}} {{ error "no routed max-delay timing path found" }}
puts [format "STUDY2 BOARD ROUTED WNS %.3f ns" [get_property SLACK $worst_path]]
write_bitstream -force [file join $OUT system_study2_board.bit]
set hwh [glob -nocomplain \\
    [file join $OUT proj *.gen sources_1 bd system hw_handoff system.hwh] \\
    [file join $OUT proj *.srcs sources_1 bd system hw_handoff system.hwh]]
if {{$hwh eq ""}} {{ error "system.hwh was not generated" }}
file copy -force [lindex $hwh 0] [file join $OUT system_study2_board.hwh]
puts "STUDY2 BOARD BITSTREAM DONE"
'''


def write_outputs(spec: dict, selected_designs: list[dict], chosen: dict, sources: list[dict]):
    if RESULT_PATH.exists():
        raise BoardInputError(
            f"refusing existing live-result path during generation: {rel(RESULT_PATH)}"
        )
    duts = OUT / "duts"
    goldens = OUT / "goldens"
    duts.mkdir(parents=True, exist_ok=True)
    goldens.mkdir(parents=True, exist_ok=True)
    expected_duts = set()
    expected_goldens = set()
    entries = []
    selections = []
    sel = 0
    for design_row in selected_designs:
        design = design_row["design"]
        stub = design.replace("_8b", "").replace("_", "")
        for arm in ARMS:
            pick = chosen[(arm, design)]
            representative = pick["representative"]
            src = representative["rtl"]
            dst = duts / f"{representative['module']}.v"
            shutil.copyfile(src, dst)
            expected_duts.add(dst.name)
            entry_name = f"{arm}_{stub}"
            golden_dir = goldens / entry_name
            golden_dir.mkdir(parents=True, exist_ok=True)
            golden_path = golden_dir / "golden.py"
            golden_path.write_text(golden_text(design_row), encoding="utf-8", newline="\n")
            expected_goldens.add(golden_path.resolve())
            entry = {
                "sel": sel,
                "entry": entry_name,
                "role": "dut",
                "arm": arm,
                "design": design,
                "family": design_row["family"],
                "regime": design_row["regime"],
                "module": representative["module"],
                "rtl": src,
                "copied_rtl": dst,
                "golden": golden_path,
            }
            entries.append(entry)
            selections.append(
                {
                    "sel": sel,
                    "entry": entry_name,
                    "role": "dut",
                    "arm": arm,
                    "design": design,
                    "family": design_row["family"],
                    "regime": design_row["regime"],
                    "selection_rule": spec["candidate_selection"]["rule"],
                    "total_arm_samples": pick["total_arm_samples"],
                    "total_arm_correct": pick["total_arm_correct"],
                    "selected_rtl_occurrences": pick["selected_rtl_occurrences"],
                    "selected_emitted_sha256": pick["selected_emitted_sha256"],
                    "population_unique_rtl": pick["population_unique_rtl"],
                    "representative_module": representative["module"],
                    "identity_group_members": pick["identity_group_members"],
                    "post_selection_ppa_gate": pick["post_selection_ppa_gate"],
                    "provenance": {
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

    stale_duts = [path for path in duts.glob("*.v") if path.name not in expected_duts]
    stale_goldens = [
        path for path in goldens.glob("*/golden.py") if path.resolve() not in expected_goldens
    ]
    if stale_duts or stale_goldens:
        raise BoardInputError("refusing stale DUT or golden files in Study 2 board output")

    canary_rtl = ROOT / "rtl_library" / "echo8b" / "design.v"
    canary_golden = ROOT / "rtl_library" / "echo8b" / "golden.py"
    entries.append(
        {
            "sel": sel, "entry": "echo8b", "role": "canary", "arm": None,
            "design": "echo8b", "family": "canary", "regime": None,
            "module": "echo8b", "rtl": canary_rtl, "copied_rtl": canary_rtl,
            "golden": canary_golden,
        }
    )

    wires = "\n".join(f"    wire [15:0] y{entry['sel']};" for entry in entries)
    insts = "\n".join(
        f"    {entry['module']} u{entry['sel']} (.clk(clk), .rst_n(dut_rst_n), "
        f".x(cnt[7:0]), .y(y{entry['sel']}));"
        for entry in entries
    )
    cases = "\n".join(
        f"            6'd{entry['sel']}: probe = y{entry['sel']};" for entry in entries
    )
    (OUT / "dut_top.v").write_text(
        f'''`timescale 1ns/1ps
// Generated by gen_study2_board.py; selection rules are frozen separately.
module dut_top (
    input wire clk, input wire rst_n, input wire cap, input wire [5:0] sel,
    output reg [15:0] probe
);
    wire dut_rst_n = rst_n & cap;
    reg [31:0] cnt;
    always @(posedge clk)
        if (!rst_n || !cap) cnt <= 32'b0;
        else cnt <= cnt + 1'b1;
{wires}
{insts}
    always @(*) begin
        case (sel)
{cases}
            default: probe = 16'b0;
        endcase
    end
endmodule
''',
        encoding="utf-8", newline="\n",
    )
    (OUT / "build_study2_board.tcl").write_text(
        build_tcl(entries), encoding="utf-8", newline="\n"
    )
    sels = collections.OrderedDict()
    for entry in entries:
        sels[entry["entry"]] = {
            "sel": entry["sel"], "role": entry["role"],
            "module": entry["module"], "arm": entry["arm"],
            "design": entry["design"], "family": entry["family"],
            "regime": entry["regime"], "golden": rel(entry["golden"]),
            "golden_sha256": sha256(entry["golden"]),
        }
    (OUT / "study2_board_sels.json").write_text(
        json.dumps(sels, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    generated_outputs = {
        "dut_top": {
            "path": rel(OUT / "dut_top.v"),
            "sha256": sha256(OUT / "dut_top.v"),
        },
        "build_tcl": {
            "path": rel(OUT / "build_study2_board.tcl"),
            "sha256": sha256(OUT / "build_study2_board.tcl"),
        },
        "sels": {
            "path": rel(OUT / "study2_board_sels.json"),
            "sha256": sha256(OUT / "study2_board_sels.json"),
        },
        "bitstream_expected": rel(OUT / "out" / "system_study2_board.bit"),
        "hwh_expected": rel(OUT / "out" / "system_study2_board.hwh"),
        "live_result_reserved": rel(RESULT_PATH),
    }
    manifest = {
        "schema": "study2_board_selection/1",
        "status": spec["status"],
        "git_head_at_generation": git_head(),
        "spec": rel(SPEC_PATH),
        "spec_sha256_lf": sha256_lf(SPEC_PATH),
        "protocol_amendment": rel(AMENDMENT_PATH),
        "protocol_amendment_sha256": sha256(AMENDMENT_PATH),
        "primary_outcome_unchanged": spec["primary_outcome_unchanged"],
        "design_selection": {
            "rule": spec["design_selection"]["rule"],
            "eligibility": spec["design_selection"]["eligibility"],
            "uses_policy_or_ppa_outcomes": True,
            "outcome_use_limited_to": "binary correctness eligibility only",
            "uses_reward_fmax_resource_or_power": False,
            "designs": [
                {
                    "design": row["design"], "family": row["family"],
                    "regime": row["regime"],
                    "selection_digest": row["selection_digest"],
                    "correctness_eligibility": row["correctness_eligibility"],
                }
                for row in selected_designs
            ],
        },
        "candidate_selection": spec["candidate_selection"],
        "source_artifacts": sorted(sources, key=lambda row: (row["arm"], row["directory"])),
        "selections": selections,
        "canary": sels["echo8b"],
        "measurement": spec["measurement"],
        "generated_outputs": generated_outputs,
    }
    (OUT / "selection_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    return entries, manifest


def self_check(entries: list[dict], n: int = 1200) -> None:
    work = OUT / ".self_check_work"
    work.mkdir(parents=True, exist_ok=True)
    stim = (np.arange(n) & 0xFF).astype(np.uint16)
    failures = 0
    try:
        for entry in entries:
            spec = importlib.util.spec_from_file_location(
                "study2_board_" + entry["entry"], entry["golden"]
            )
            module = importlib.util.module_from_spec(spec)
            assert spec.loader is not None
            spec.loader.exec_module(module)
            golden = module.compute_golden(n).astype(np.uint16)
            candidate_path = work / "cand.v"
            tb_path = work / "tb.v"
            stim_path = work / "stim.hex"
            vvp_path = work / "a.vvp"
            candidate_path.write_text(
                entry["copied_rtl"].read_text(encoding="utf-8"), encoding="utf-8"
            )
            tb_path.write_text(oracle._tb(entry["module"], n, 8), encoding="utf-8")
            stim_path.write_text(
                "\n".join(f"{int(value):x}" for value in stim) + "\n", encoding="utf-8"
            )
            compile_run = subprocess.run(
                ["iverilog", "-g2012", "-o", str(vvp_path),
                 str(candidate_path), str(tb_path)],
                capture_output=True, text=True, timeout=60,
            )
            if compile_run.returncode:
                print(f"  {entry['entry']:18s} COMPILE FAIL")
                failures += 1
                continue
            sim = subprocess.run(
                ["vvp", str(vvp_path)], capture_output=True, text=True,
                cwd=work, timeout=60,
            )
            trace = oracle._parse_trace(sim.stdout)
            if sim.returncode or trace is None:
                print(f"  {entry['entry']:18s} SIM FAIL")
                failures += 1
                continue
            best = 0.0
            for shift in range(9):
                for actual, expected in ((trace[8:], golden[shift:]),
                                         (trace[8 + shift:], golden)):
                    length = min(len(actual), len(expected), 1024)
                    if length >= 64:
                        best = max(best, float(np.mean(actual[:length] == expected[:length])))
            ok = best >= 0.999
            failures += int(not ok)
            print(f"  {entry['entry']:18s} match={best:.4f} {'OK' if ok else 'MISMATCH'}")
    finally:
        shutil.rmtree(work, ignore_errors=True)
    if failures:
        raise BoardInputError(f"{failures} DUT/golden self-check failures")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="run all DUT/golden Icarus checks")
    args = parser.parse_args()
    spec = read_json(SPEC_PATH)
    verify_spec(spec)
    sealed = read_json(SEALED_PATH)
    arm_stats, sources = load_arm_stats(sealed)
    designs = select_designs(spec, sealed, arm_stats)
    ppa_rows = load_compiled_rows()
    chosen, sources = select_candidates(
        spec, designs, arm_stats, ppa_rows, sources
    )
    entries, manifest = write_outputs(spec, designs, chosen, sources)
    print("Study 2 board selection:")
    for row in manifest["selections"]:
        print(
            f"  sel {row['sel']:2d}: {row['entry']:18s} "
            f"{row['representative_module']} count={row['selected_rtl_occurrences']}"
        )
    print(f"  sel {entries[-1]['sel']:2d}: echo8b (canary)")
    if args.check:
        print("self-check:")
        self_check(entries)
    print(f"wrote {rel(OUT)}/selection_manifest.json and build inputs")
    print(f"live result remains absent: {not RESULT_PATH.exists()}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (BoardInputError, OSError, ValueError, subprocess.TimeoutExpired) as exc:
        raise SystemExit(f"Study 2 board input error: {exc}")
