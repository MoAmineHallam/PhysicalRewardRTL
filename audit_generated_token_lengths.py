#!/usr/bin/env python3
"""Audit generated RTL length with the frozen model tokenizer.

The historical v8 evaluation retained only oracle-correct RTL candidates.  The
result is therefore explicitly conditional on correctness; it must not be
described as the length of every generation.  Candidate multiplicity from each
fmax_manifest.json is preserved so duplicate outputs count as often as they
were sampled.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
import statistics
from typing import Dict, Iterable, List


DEFAULT_DIRS = [
    "rtl/holdout_eval_v8_firfirr",
    "rtl/holdout_eval_v8_iirmed",
    "rtl/holdout_eval_v8_poly",
]
POLICIES = ("base", "sft", "grpo")
TOKENIZER_NAMES = (
    "tokenizer.json",
    "tokenizer_config.json",
    "special_tokens_map.json",
    "added_tokens.json",
    "vocab.json",
    "merges.txt",
)


class TokenAuditError(RuntimeError):
    pass


def sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def weighted_median(values: Iterable[tuple[int, int]]) -> float:
    ordered = sorted(values)
    total = sum(weight for _, weight in ordered)
    if total <= 0:
        raise TokenAuditError("cannot take a weighted median with zero weight")
    expanded_middle = (total - 1) / 2
    cumulative = 0
    lower = upper = None
    for value, weight in ordered:
        previous = cumulative
        cumulative += weight
        if lower is None and expanded_middle < cumulative:
            lower = value
        if total % 2 == 0 and previous <= total / 2 < cumulative:
            upper = value
        if total % 2 == 1 and lower is not None:
            upper = lower
        if lower is not None and upper is not None:
            break
    if total % 2 == 0:
        # For an even sample, find the values at zero-indexed positions n/2-1
        # and n/2 without materialising repeated candidates.
        positions = (total // 2 - 1, total // 2)
        found: List[int] = []
        cumulative = 0
        for value, weight in ordered:
            cumulative += weight
            for position in positions[len(found):]:
                if position < cumulative:
                    found.append(value)
                else:
                    break
            if len(found) == 2:
                return statistics.mean(found)
    if lower is None:
        raise TokenAuditError("weighted median calculation failed")
    return float(lower)


def load_rows(root: str, directories: List[str], tokenizer) -> tuple[list, dict, str]:
    rows = []
    total_draws: Dict[str, int] = collections.defaultdict(int)
    source_digest = hashlib.sha256()
    seen_policy_design = set()
    for relative in directories:
        directory = os.path.join(root, relative)
        manifest_path = os.path.join(directory, "fmax_manifest.json")
        summary_path = os.path.join(directory, "holdout_summary.json")
        if not os.path.isfile(manifest_path) or not os.path.isfile(summary_path):
            raise TokenAuditError(f"missing manifest or summary in {relative}")
        manifest = json.load(open(manifest_path, encoding="utf-8"))
        summary = json.load(open(summary_path, encoding="utf-8"))
        source_digest.update(relative.encode() + b"\0")
        source_digest.update(bytes.fromhex(sha256_file(manifest_path)))
        source_digest.update(bytes.fromhex(sha256_file(summary_path)))
        for policy in POLICIES:
            for design, record in summary.get(policy, {}).items():
                key = (policy, design)
                if key in seen_policy_design:
                    raise TokenAuditError(f"duplicate policy/design summary: {key}")
                seen_policy_design.add(key)
                total_draws[policy] += int(record["n"])
        for module, record in manifest.items():
            policy = record.get("policy")
            if policy not in POLICIES:
                continue
            rtl_path = os.path.join(directory, module + ".sv")
            if not os.path.isfile(rtl_path):
                raise TokenAuditError(f"missing retained candidate: {rtl_path}")
            text = open(rtl_path, encoding="utf-8").read()
            source_digest.update((relative + "/" + module + ".sv").encode() + b"\0")
            source_digest.update(bytes.fromhex(sha256_file(rtl_path)))
            rows.append({
                "policy": policy,
                "design": record["design"],
                "count": int(record["count"]),
                "tokens": len(tokenizer.encode(text, add_special_tokens=False)),
                "characters": len(text),
                "lines": len(text.splitlines()),
            })
    return rows, dict(total_draws), source_digest.hexdigest()


def summarize(rows: list, total_draws: dict) -> dict:
    designs_by_policy = {}
    for policy in POLICIES:
        designs_by_policy[policy] = {
            row["design"] for row in rows if row["policy"] == policy
        }
    common_designs = set.intersection(*designs_by_policy.values())
    policies = {}
    for policy in POLICIES:
        selected = [row for row in rows if row["policy"] == policy]
        if not selected:
            raise TokenAuditError(f"no retained candidates for {policy}")
        by_design = collections.defaultdict(list)
        for row in selected:
            by_design[row["design"]].append(row)
        correct_draws = sum(row["count"] for row in selected)

        def weighted_mean(field: str, subset: list) -> float:
            weight = sum(row["count"] for row in subset)
            return sum(row[field] * row["count"] for row in subset) / weight

        design_means = {
            design: weighted_mean("tokens", candidates)
            for design, candidates in by_design.items()
        }
        policies[policy] = {
            "total_generated_draws": total_draws[policy],
            "retained_correct_draws": correct_draws,
            "retained_correct_rate": correct_draws / total_draws[policy],
            "designs_with_retained_correct": len(by_design),
            "distinct_retained_correct": len(selected),
            "tokens_mean_correct_draw_weighted": weighted_mean("tokens", selected),
            "tokens_median_correct_draw_weighted": weighted_median(
                (row["tokens"], row["count"]) for row in selected),
            "tokens_mean_design_balanced_conditional_correct": statistics.mean(
                design_means.values()),
            "tokens_mean_common_designs_conditional_correct": statistics.mean(
                design_means[design] for design in sorted(common_designs)),
            "characters_mean_correct_draw_weighted": weighted_mean(
                "characters", selected),
            "lines_mean_correct_draw_weighted": weighted_mean("lines", selected),
        }
    return {"common_design_count": len(common_designs), "policies": policies}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=os.path.dirname(os.path.abspath(__file__)))
    parser.add_argument("--tokenizer", required=True)
    parser.add_argument("--dirs", nargs="+", default=DEFAULT_DIRS)
    parser.add_argument("--out", default="token_length_audit_v8.json")
    args = parser.parse_args()

    from transformers import AutoTokenizer, __version__ as transformers_version

    tokenizer = AutoTokenizer.from_pretrained(
        args.tokenizer, local_files_only=True, trust_remote_code=True)
    rows, total_draws, source_digest = load_rows(
        os.path.abspath(args.root), args.dirs, tokenizer)
    result = {
        "schema": "generated_token_length_audit/1",
        "scope": "historical v8 retained oracle-correct RTL only",
        "caveat": (
            "Incorrect and extraction-failed generations were not retained, so "
            "token length is conditional on oracle correctness and is not the "
            "mean length of every generated sample."
        ),
        "weighting": (
            "candidate multiplicity within policy/design; design-balanced values "
            "are also reported"
        ),
        "tokenizer_class": tokenizer.__class__.__name__,
        "tokenizer_vocab_size": len(tokenizer),
        "transformers_version": transformers_version,
        "tokenizer_file_sha256": {
            name: sha256_file(os.path.join(args.tokenizer, name))
            for name in TOKENIZER_NAMES
            if os.path.isfile(os.path.join(args.tokenizer, name))
        },
        "source_directories": args.dirs,
        "source_content_sha256": source_digest,
    }
    result.update(summarize(rows, total_draws))
    means = {
        policy: result["policies"][policy]["tokens_mean_correct_draw_weighted"]
        for policy in POLICIES
    }
    result["comparisons"] = {
        "grpo_vs_base_mean_correct_token_ratio": means["grpo"] / means["base"],
        "grpo_vs_sft_mean_correct_token_ratio": means["grpo"] / means["sft"],
        "sft_vs_base_mean_correct_token_ratio": means["sft"] / means["base"],
    }
    output = args.out if os.path.isabs(args.out) else os.path.join(args.root, args.out)
    with open(output, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(result, handle, indent=1, sort_keys=True)
        handle.write("\n")
    print(json.dumps(result, indent=1, sort_keys=True))
    print(f"audit -> {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
