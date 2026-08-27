#!/usr/bin/env python3
"""No-launch data planning/auditing for the PPA-RTL DPO adaptation."""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class DataError(RuntimeError):
    pass


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_text(text: str) -> str:
    return sha_bytes(text.replace("\r\n", "\n").encode("utf-8"))


def file_sha(path: Path) -> str:
    """Return SHA-256 of the exact bytes stored on disk."""
    return sha_bytes(path.read_bytes())


def read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise DataError(f"cannot read {path}: {exc}") from exc


def atomic_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                   encoding="utf-8", newline="\n")
    tmp.replace(path)


def rank(salt: str, name: str) -> str:
    return sha_text(f"{salt}\0{name}")


def generate_plan(config: dict) -> dict:
    import gen_sft_corpus as corpus

    spec = config["prospective_label_plan"]
    eligible = []
    for name, family, description, styles in corpus.designs(exclude_holdout=True):
        if family == "cordic":
            continue
        reference = styles.get("ref") or next(iter(styles.values()))
        eligible.append({
            "design": name, "family": family,
            "prompt": corpus.make_prompt(description, reference),
            "reference_rtl": reference,
        })
    if len(eligible) != spec["eligible_train_prompts"]:
        raise DataError(f"train split drift: {len(eligible)} != {spec['eligible_train_prompts']}")
    selected = []
    for family, quota in spec["family_quotas"].items():
        pool = [row for row in eligible if row["family"] == family]
        pool.sort(key=lambda row: (rank(spec["selection_salt"], row["design"]), row["design"]))
        if len(pool) < quota:
            raise DataError(f"family {family} has {len(pool)} prompts for quota {quota}")
        selected.extend(pool[:quota])
    if len(selected) != spec["selected_prompts"]:
        raise DataError("selected prompt count drift")
    poly = [row for row in selected if row["family"] == "poly"]
    four = max(poly, key=lambda row: (rank(spec["selection_salt"], row["design"]), row["design"]))

    prompts, slots = [], []
    for row in sorted(selected, key=lambda value: (value["family"], value["design"])):
        n_candidates = 4 if row["design"] == four["design"] else 5
        prompt_id = sha_text(row["prompt"])
        prompts.append({
            "design": row["design"], "family": row["family"],
            "prompt": row["prompt"], "prompt_sha256": prompt_id,
            "reference_rtl": row["reference_rtl"],
            "reference_sha256": sha_text(row["reference_rtl"]),
            "candidate_slots": n_candidates,
        })
        slots.append({"slot_id": f"{row['design']}/reference", "design": row["design"],
                      "family": row["family"], "source": "catalog_reference",
                      "generation_seed": None})
        for index in range(1, n_candidates):
            digest = rank(spec["selection_salt"], f"{row['design']}\0{index}")
            slots.append({"slot_id": f"{row['design']}/sft_{index}",
                          "design": row["design"], "family": row["family"],
                          "source": "sft_v6c_out", "generation_seed": int(digest[:8], 16)})
    if len(slots) != spec["candidate_slots"]:
        raise DataError(f"slot count drift: {len(slots)}")
    return {
        "schema_version": 1, "study_id": config["study_id"],
        "status": "planned_not_generated_or_labeled",
        "selection_salt": spec["selection_salt"],
        "eligible_train_prompts": len(eligible), "selected_prompts": len(prompts),
        "family_counts": dict(collections.Counter(row["family"] for row in prompts)),
        "four_candidate_prompt": four["design"], "candidate_slots": len(slots),
        "prompts": prompts, "slots": slots,
        "prohibitions": ["no generation performed", "no oracle executed",
                          "no Vivado/EDA executed", "no training performed"],
    }


def audit_existing(config: dict) -> dict:
    source = ROOT / config["existing_rows_dry_run"]["input"]
    manifest = read_json(source)
    rows = manifest.get("rows", [])
    errors, records, producer_counts = [], [], collections.Counter()
    underlying = collections.Counter()
    content_by_design = collections.defaultdict(set)
    import gen_sft_corpus as corpus
    for row in rows:
        design = str(row.get("design", "")).split("__")[-1]
        underlying[design] += 1
        directory = ROOT / "rtl" / Path(str(row.get("src", ""))).name
        rtl_path = directory / f"{row.get('mod')}.sv"
        ppa_path, fmax_manifest_path = directory / "ppa.jsonl", directory / "fmax_manifest.json"
        if not rtl_path.is_file() or not ppa_path.is_file() or not fmax_manifest_path.is_file():
            errors.append(f"missing source/label evidence for {row.get('key')}")
            continue
        fmax_rows = {}
        for line in ppa_path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                item = json.loads(line)
            except ValueError:
                continue
            fmax_rows[item.get("module")] = item
        measured = fmax_rows.get(row.get("mod"), {})
        if not measured.get("compiled") or not math.isclose(float(measured.get("fmax_mhz", -1)),
                                                              float(row.get("fmax", -2)),
                                                              rel_tol=0, abs_tol=1e-9):
            errors.append(f"label mismatch for {row.get('key')}")
        producer = "unknown_legacy_generator"
        entry = read_json(fmax_manifest_path).get(row.get("mod"), {})
        if directory.name == "policy_cmp":
            producer = str(entry.get("policy", "unknown_policy_cmp"))
        producer_counts[producer] += 1
        rtl_hash = file_sha(rtl_path)
        content_by_design[design].add(rtl_hash)
        records.append({"key": row.get("key"), "design": design,
                        "source_directory": directory.name, "producer": producer,
                        "rtl_sha256": rtl_hash, "fmax_mhz": float(row["fmax"]),
                        "held_out": bool(corpus.is_holdout(design)),
                        "row_level_generation_seed_present": False,
                        "two_seed_1024_vector_oracle_evidence_present": False})
    invalid_reasons = [
        "candidate producers are mixed (known SFT/GRPO plus unknown legacy generators), not a frozen sample from the same SFT reference policy",
        "rows do not carry per-candidate generation seeds or sampling configurations",
        "rows do not carry the required two-seed, 1024-vector functional-oracle verdicts",
        "the 229 rows cover 25 previously chosen underlying designs rather than the prospectively selected stratified prompt subset",
    ]
    if errors:
        invalid_reasons.append("one or more source/label consistency checks failed")
    return {
        "schema_version": 1, "study_id": config["study_id"],
        "audit": "existing training rows as possible DPO preference source",
        "input": str(source.relative_to(ROOT)).replace("\\", "/"),
        "input_sha256": file_sha(source), "rows": len(rows),
        "underlying_designs": len(underlying),
        "designs_with_at_least_two_rows": sum(value >= 2 for value in underlying.values()),
        "unique_rtl": sum(len(value) for value in content_by_design.values()),
        "held_out_rows": sum(record["held_out"] for record in records),
        "producer_counts": dict(producer_counts), "consistency_errors": errors,
        "scientifically_valid_for_dpo_construction": False,
        "verdict": "DO_NOT_CONSTRUCT_PREFERENCES_FROM_EXISTING_ROWS",
        "invalid_reasons": invalid_reasons,
        "records": records,
        "actions_performed": ["read existing manifests", "hash existing RTL",
                              "cross-check implementation labels"],
        "actions_not_performed": ["candidate generation", "oracle simulation",
                                  "Vivado/EDA", "DPO training"],
    }


def load_jsonl(path: Path) -> list[dict]:
    out = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            try:
                out.append(json.loads(line))
            except ValueError as exc:
                raise DataError(f"malformed JSON at {path}:{number}") from exc
    return out


def build_preferences(config: dict, plan: dict, labels: list[dict]) -> list[dict]:
    slots = {row["slot_id"]: row for row in plan["slots"]}
    if len(labels) != len(slots) or {row.get("slot_id") for row in labels} != set(slots):
        raise DataError("labels must cover every frozen slot exactly once")
    prompts = {row["design"]: row for row in plan["prompts"]}
    grouped = collections.defaultdict(list)
    for row in labels:
        slot = slots[row["slot_id"]]
        if row.get("design") != slot["design"] or row.get("source") != slot["source"]:
            raise DataError(f"slot identity mismatch: {row.get('slot_id')}")
        checks = row.get("oracle_checks")
        if checks != [{"seed": 1, "n": 1024, "correct": True},
                      {"seed": 2, "n": 1024, "correct": True}]:
            raise DataError(f"oracle gate mismatch: {row['slot_id']}")
        if row.get("eda_attempted") is not True:
            raise DataError(f"EDA budget row missing: {row['slot_id']}")
        rtl = row.get("rtl")
        if not isinstance(rtl, str) or sha_text(rtl) != row.get("rtl_sha256"):
            raise DataError(f"RTL/hash mismatch: {row['slot_id']}")
        score = float(row.get("fmax_mhz", -1))
        if score < 0 or not math.isfinite(score):
            raise DataError(f"invalid failure-aware score: {row['slot_id']}")
        grouped[row["design"]].append((score, row["rtl_sha256"], row))
    pairs = []
    for design, candidates in sorted(grouped.items()):
        ordered = sorted(candidates, key=lambda value: (value[0], value[1]))
        if math.isclose(ordered[0][0], ordered[-1][0], rel_tol=0, abs_tol=1e-12):
            continue
        lo, hi = ordered[0], ordered[-1]
        span = hi[0] - lo[0]
        pairs.append({"prompt_id": prompts[design]["prompt_sha256"],
                      "design": design, "prompt": prompts[design]["prompt"],
                      "chosen": hi[2]["rtl"], "rejected": lo[2]["rtl"],
                      "chosen_fmax_mhz": hi[0], "rejected_fmax_mhz": lo[0],
                      "chosen_normalized": 1.0, "rejected_normalized": 0.0,
                      "within_prompt_span_mhz": span})
    return pairs


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("plan", "audit-existing", "build-preferences"))
    parser.add_argument("--config", default=str(HERE / "config.json"))
    parser.add_argument("--plan", default=str(HERE / "label_plan.json"))
    parser.add_argument("--labels", default="")
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    try:
        config = read_json(Path(args.config))
        if args.action == "plan":
            value = generate_plan(config)
            atomic_json(Path(args.out), value)
            summary = {
                "status": value["status"],
                "eligible_train_prompts": value["eligible_train_prompts"],
                "selected_prompts": value["selected_prompts"],
                "candidate_slots": value["candidate_slots"],
                "family_counts": value["family_counts"],
                "four_candidate_prompt": value["four_candidate_prompt"],
            }
        elif args.action == "audit-existing":
            value = audit_existing(config)
            atomic_json(Path(args.out), value)
            summary = {
                "rows": value["rows"],
                "underlying_designs": value["underlying_designs"],
                "held_out_rows": value["held_out_rows"],
                "consistency_errors": len(value["consistency_errors"]),
                "scientifically_valid_for_dpo_construction":
                    value["scientifically_valid_for_dpo_construction"],
                "verdict": value["verdict"],
            }
        else:
            if not args.labels:
                raise DataError("--labels is required for build-preferences")
            plan = read_json(Path(args.plan))
            pairs = build_preferences(config, plan, load_jsonl(Path(args.labels)))
            if not pairs:
                raise DataError("no non-tied preference pairs")
            output = Path(args.out)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in pairs),
                              encoding="utf-8", newline="\n")
            summary = {"pairs": len(pairs)}
    except (DataError, OSError, ValueError) as exc:
        print(f"data preparation error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
