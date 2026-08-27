#!/usr/bin/env python3
"""Fail-closed validator for the no-launch PPA-RTL DPO preparation package."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from prepare_data import audit_existing, file_sha, generate_plan, read_json


class ValidationError(RuntimeError):
    pass


HEX64 = re.compile(r"^[0-9a-f]{64}$")
TIMING_MANIFEST = "2e0674f96c57be3864a6fab7683b0edc76f732762f78547d5e6a3e8efc17e194"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def require_equal(actual, expected, label: str) -> None:
    if actual != expected:
        raise ValidationError(f"{label}: {actual!r} != {expected!r}")


def canonical_sha(value) -> str:
    payload = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def validate_config(config: dict) -> None:
    require_equal(config.get("schema_version"), 1, "schema_version")
    require_equal(config.get("study_id"), "ppa_rtl_dpo_baseline_v1", "study_id")
    require_equal(config.get("status"), "prepared_not_launched", "status")
    require_equal(config.get("provenance_hash_policy"),
                  "sha256_raw_bytes_no_newline_normalization",
                  "provenance hash policy")

    identity = config.get("method_identity", {})
    require_equal(identity.get("official_reproduction"), False,
                  "method_identity.official_reproduction")
    require_equal(
        identity.get("permitted_label"),
        "independent adaptation of PPA-RTL's performance-only best-versus-worst DPO method",
        "method_identity.permitted_label",
    )
    require("independent adaptation" in identity.get("name", "").lower(),
            "method name must disclose independent-adaptation status")
    require("reproduction" not in identity.get("name", "").lower(),
            "method name must not imply reproduction")

    source = config.get("primary_sources", {})
    require_equal(source.get("official_code_or_training_checkpoint_found"), False,
                  "primary_sources.official_code_or_training_checkpoint_found")
    require(source.get("paper", {}).get("ieee_document") == "11132897",
            "wrong primary-paper IEEE document")
    require(source.get("official_preference_dataset", "").startswith("https://huggingface.co/"),
            "official preference dataset URL missing")

    matched = config.get("matched_scope", {})
    require_equal(matched.get("initial_policy"), "sft_v6c_out", "initial policy")
    require_equal(matched.get("frozen_reference_policy"), "sft_v6c_out",
                  "frozen reference policy")
    require_equal(matched.get("eda_performance_label_budget"), 229, "EDA-label budget")
    require_equal(matched.get("optimizer_updates_per_seed"), 276, "update budget")
    require_equal(matched.get("training_seeds"), [1, 2], "training seeds")
    require_equal(matched.get("evaluation_samples_per_design_per_seed"), 24,
                  "evaluation draw budget")
    require_equal(matched.get("failure_score_mhz"), 0.0, "failure score")
    require_equal(matched.get("correctness_gate"), {
        "oracle_seeds": [1, 2], "vectors_per_seed": 1024, "must_pass_both": True,
    }, "correctness gate")

    label_plan = config.get("prospective_label_plan", {})
    require_equal(label_plan.get("eligible_train_prompts"), 145, "eligible prompts")
    require_equal(label_plan.get("selected_prompts"), 46, "selected prompts")
    require_equal(label_plan.get("candidate_slots"), 229, "candidate slots")
    require_equal(sum(label_plan.get("family_quotas", {}).values()), 46,
                  "family quota sum")
    require_equal(label_plan.get("generation", {}).get(
        "maximum_attempts_to_obtain_a_correct_generated_slot"), 16,
        "generation attempt cap")
    no_reallocation = label_plan.get("no_reallocation", "").lower()
    require("no reallocation" in no_reallocation or "do not replace" in no_reallocation,
            "no-reallocation rule missing")

    labeling = config.get("performance_labeling", {})
    require_equal(labeling.get("tool"), "Vivado 2023.1", "Vivado version")
    require(TIMING_MANIFEST in labeling.get("go_no_go", ""),
            "final timing-gate manifest is not pinned")
    require("complete PASS" in labeling.get("go_no_go", ""),
            "timing gate must fail closed")
    require("exactly 229" in labeling.get("budget_accounting", "").lower(),
            "label budget accounting is not exact")
    require("failure consumes" in labeling.get("budget_accounting", "").lower(),
            "failed implementation must consume a label slot")
    require("no replacement" in labeling.get("budget_accounting", "").lower(),
            "failed labels must not be replaced")

    dpo = config.get("dpo_training", {})
    require_equal(dpo.get("performance_weights_power_performance_area"), [0.0, 1.0, 0.0],
                  "performance-only weights")
    require_equal(dpo.get("optimizer_updates"), 276, "DPO optimizer updates")
    require_equal(dpo.get("checkpoints_at_updates"), [138, 276], "DPO checkpoints")
    require_equal(dpo.get("reference"), "a separate frozen copy of the same SFT adapter",
                  "DPO reference")
    require("fail before training" in dpo.get("overlength_policy", "").lower(),
            "overlength handling must fail closed")

    evaluation = config.get("true_closure_evaluation", {})
    require_equal(evaluation.get("designs"), 20, "held-out designs")
    require_equal(evaluation.get("samples_per_design_per_training_seed"), 24,
                  "evaluation samples")
    require_equal(evaluation.get("generation_seeds"), {"1": 101, "2": 102},
                  "evaluation generation seeds")
    require_equal(evaluation.get("multiplicity_retained"), True,
                  "evaluation multiplicity")
    require("true timing-closure" in evaluation.get("endpoint", "").lower(),
            "primary endpoint is not true timing closure")
    require("not single-constraint" in evaluation.get("endpoint", "").lower(),
            "single-constraint proxy must be excluded from primary evaluation")
    require("implementation failure" in evaluation.get("zero_scored", []),
            "implementation failure is not zero-scored")
    require("never select the better seed" in evaluation.get("reporting", "").lower(),
            "seed-selection prohibition missing")

    choices = config.get("underspecified_adaptation_choices", [])
    require(len(choices) >= 10, "primary-paper underspecification ledger is incomplete")
    require(any("does not report DPO beta" in item for item in choices),
            "missing beta disclosure")
    require(any("TSMC 90 nm" in item for item in choices),
            "missing technology-domain disclosure")

    audit = config.get("existing_rows_dry_run", {})
    require_equal(audit.get("permitted_for_training"), False,
                  "existing-row training permission")
    require("lack" in audit.get("reason", "").lower(),
            "existing-row exclusion reason missing")

    for name, digest in config.get("frozen_inputs", {}).items():
        require(bool(HEX64.fullmatch(str(digest))), f"invalid frozen digest for {name}")
    require_equal(config.get("frozen_inputs", {}).get("ppa_synth.tcl"),
                  "3def59efc4781b477d4cace4eb21bc3ca55970c332bd35f56ec6deab00f31c72",
                  "raw-byte ppa_synth.tcl digest")
    for key in ("label_plan_sha256", "existing_rows_audit_sha256"):
        require(bool(HEX64.fullmatch(str(config.get("generated_artifacts", {}).get(key, "")))),
                f"generated artifact is not frozen: {key}")


def validate_local_hashes(config: dict) -> list[str]:
    checked = []
    for name, expected in config["frozen_inputs"].items():
        if name.endswith("_directory_manifest"):
            continue
        path = ROOT / name
        require(path.is_file(), f"missing frozen input: {name}")
        require_equal(file_sha(path), expected, f"hash for {name}")
        checked.append(name)
    return checked


def validate_generated(config: dict) -> tuple[dict, dict]:
    artifacts = config["generated_artifacts"]
    plan_path = ROOT / artifacts["label_plan"]
    audit_path = ROOT / artifacts["existing_rows_audit"]
    require(plan_path.is_file(), "frozen label plan missing")
    require(audit_path.is_file(), "existing-row audit missing")
    require_equal(file_sha(plan_path), artifacts["label_plan_sha256"],
                  "label-plan artifact hash")
    require_equal(file_sha(audit_path), artifacts["existing_rows_audit_sha256"],
                  "existing-row-audit artifact hash")
    plan, audit = read_json(plan_path), read_json(audit_path)
    require_equal(plan, generate_plan(config), "deterministically regenerated label plan")
    require_equal(audit, audit_existing(config), "deterministically regenerated row audit")

    require_equal(plan.get("status"), "planned_not_generated_or_labeled", "plan status")
    require_equal(plan.get("selected_prompts"), 46, "plan selected prompts")
    require_equal(plan.get("candidate_slots"), 229, "plan candidate slots")
    require_equal(plan.get("family_counts"), config["prospective_label_plan"]["family_quotas"],
                  "plan family quotas")
    require_equal(len({row["slot_id"] for row in plan["slots"]}), 229,
                  "unique slot identities")
    require_equal(sum(row["source"] == "catalog_reference" for row in plan["slots"]), 46,
                  "catalog reference slots")
    generated_seeds = [row["generation_seed"] for row in plan["slots"]
                       if row["source"] == "sft_v6c_out"]
    require_equal(len(generated_seeds), 183, "generated SFT slots")
    require_equal(len(set(generated_seeds)), 183, "unique generation seeds")

    require_equal(audit.get("rows"), 229, "audited existing rows")
    require_equal(audit.get("underlying_designs"), 25, "audited underlying designs")
    require_equal(audit.get("held_out_rows"), 0, "held-out rows in legacy pool")
    require_equal(audit.get("consistency_errors"), [], "legacy label consistency")
    require_equal(audit.get("scientifically_valid_for_dpo_construction"), False,
                  "legacy rows scientific validity")
    require_equal(audit.get("verdict"),
                  "DO_NOT_CONSTRUCT_PREFERENCES_FROM_EXISTING_ROWS", "legacy audit verdict")
    return plan, audit


def validate_no_runtime_artifacts() -> None:
    forbidden = [
        HERE / "labels.jsonl", HERE / "preferences.jsonl", HERE / ".launched",
        HERE / "runs", HERE / "results", HERE / "checkpoints",
    ]
    found = [str(path.relative_to(ROOT)).replace("\\", "/")
             for path in forbidden if path.exists()]
    require(not found, f"preparation package contains runtime artifacts: {found}")


def validate(config_path: Path = HERE / "config.json") -> dict:
    config = read_json(config_path)
    validate_config(config)
    checked = validate_local_hashes(config)
    plan, audit = validate_generated(config)
    validate_no_runtime_artifacts()
    return {
        "status": "PASS",
        "study_id": config["study_id"],
        "package_state": config["status"],
        "local_frozen_inputs_checked": checked,
        "remote_directory_manifest_digests_format_checked_only": [
            "sft_v6c_out_directory_manifest", "base_model_directory_manifest",
        ],
        "selected_prompts": plan["selected_prompts"],
        "candidate_slots": plan["candidate_slots"],
        "legacy_rows_audited": audit["rows"],
        "legacy_rows_permitted_for_preferences": False,
        "generation_or_oracle_or_eda_or_training_performed": False,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(HERE / "config.json"))
    args = parser.parse_args(argv)
    try:
        report = validate(Path(args.config))
    except (ValidationError, OSError, ValueError) as exc:
        print(f"validation error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
