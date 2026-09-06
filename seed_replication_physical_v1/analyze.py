"""Compute per-policy endpoints only after all frozen candidates finish."""
import json
import statistics
from pathlib import Path
from seed_replication_physical_v1.run import HERE, ROOT, verify_manifest, completed_valid
from eval_sealed import load_split


def main():
    manifest, identity = verify_manifest()
    split = load_split(str(ROOT / "sealed_split.json"))
    results = {}
    for row in manifest["candidates"]:
        path = HERE / "results" / row["candidate_id"] / "closure_result.json"
        if not path.exists():
            raise RuntimeError("Physical campaign incomplete: " + row["module"])
        results[row["module"]] = completed_valid(path, identity)
    policies = {}
    for policy in manifest["policies"]:
        per_design = {}
        for design in split:
            rows = [r for r in manifest["candidates"] if r["policy"] == policy and r["design"] == design["design"]]
            score = sum(r["count"] * float(results[r["module"]]["closure_fmax_mhz"]) / r["n"] for r in rows)
            per_design[design["design"]] = score
        policies[policy] = {"per_design_mhz": per_design,
            "equal_design_mean_mhz": statistics.mean(per_design.values()),
            "failed_candidates": sum(results[r["module"]]["status"] != "COMPLETE" for r in manifest["candidates"] if r["policy"] == policy)}
    sft = policies["sft"]["per_design_mhz"]
    for policy, value in policies.items():
        value["paired_sft_difference_mhz"] = statistics.mean(value["per_design_mhz"][d] - sft[d] for d in sft)
    output = {"scope": "post-primary additional-seed physical endpoint", "manifest_sha256_lf": identity,
              "policies": policies}
    (HERE / "analysis.json").write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
