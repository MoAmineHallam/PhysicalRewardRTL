#!/usr/bin/env python3
"""Gate 0 physical step: gather circuits for Vivado, then apply the frozen analysis.

    python student/gate0_physical.py collect --out gate0/vivado      # on the server
    # laptop, in the old fpga checkout:
    #   python run_ppa.py --dir <vivado dir> --out <vivado dir>/ppa.jsonl --period 5.0
    python student/gate0_physical.py analyze --vivado gate0/vivado   # anywhere

``collect`` writes each distinct oracle-correct candidate once (deduplicated
across every run by normalized RTL, as in ``eval_sealed``) with its module
renamed to its file stem, plus ``candidate_map.json`` linking it back to every
run and multiplicity.  ``analyze`` implements GATE0_PROTOCOL_20261001.md:
q, mu and F per design, arm-minus-fp16 contrasts, stratified paired design
bootstrap, and the decision rule.  Strata hold only two or three designs, so an
unstratified interval is also reported as a descriptive sensitivity check; the
decision uses the frozen stratified interval only.  It uses only the standard library.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
import sys
from collections import defaultdict
from typing import Dict, List, Optional, Sequence, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(os.path.dirname(HERE), "gate0")
RESAMPLES = 10_000
BOOTSTRAP_SEED = 20261001


def normalised_rtl(rtl: str) -> str:
    """Same normalisation ``eval_sealed`` uses for deduplication."""
    body = re.sub(r"\bmodule\s+\w+", "module M", rtl, count=1)
    return re.sub(r"\s+", " ", body).strip()


def load_json(path: str):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def run_records(plan: dict, allow_partial: bool) -> List[dict]:
    done, missing = [], []
    for run in plan["runs"]:
        if os.path.isfile(os.path.join(run["out_dir"], "generation_config.json")):
            done.append(run)
        else:
            missing.append(run["id"])
    if missing and not allow_partial:
        raise SystemExit(f"runs not complete yet: {', '.join(missing)} "
                         "(use --allow-partial to start Vivado early)")
    return done


def collect(args: argparse.Namespace) -> None:
    plan = load_json(os.path.join(WORK, "plan.json"))
    os.makedirs(args.out, exist_ok=True)
    map_path = os.path.join(args.out, "candidate_map.json")
    cmap: Dict[str, dict] = load_json(map_path) if os.path.isfile(map_path) else {}
    added = 0
    for run in run_records(plan, args.allow_partial):
        manifest = load_json(os.path.join(run["out_dir"], "fmax_manifest.json"))
        for module, rec in manifest.items():
            with open(os.path.join(run["out_dir"], module + ".sv"), encoding="ascii") as handle:
                rtl = handle.read()
            key = hashlib.sha256((rec["design"] + "\n" + normalised_rtl(rtl)).encode()).hexdigest()
            stem = f"g0_{rec['design']}__{key[:12]}"
            entry = cmap.setdefault(stem, {"design": rec["design"], "family": rec["family"],
                                           "regime": rec["regime"], "key": key, "members": []})
            member = {"run": run["id"], "module": module, "count": rec["count"]}
            if member not in entry["members"]:
                entry["members"].append(member)
            path = os.path.join(args.out, stem + ".sv")
            if not os.path.isfile(path):
                renamed, n = re.subn(r"\bmodule\s+" + re.escape(module) + r"\b",
                                     "module " + stem, rtl, count=1)
                if n != 1:
                    raise SystemExit(f"{module}: module declaration not found")
                with open(path, "w", encoding="ascii", newline="\n") as handle:
                    handle.write(renamed)
                added += 1
    with open(map_path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(cmap, handle, indent=1, sort_keys=True)
        handle.write("\n")
    print(f"{len(cmap)} distinct circuits in {args.out} ({added} new this time)")


# ----------------------------------------------------------------- analysis

def design_table(plan: dict, cmap: dict, ppa: Dict[str, dict]) -> Dict[str, Dict[str, dict]]:
    """table[run][design] = {n, correct, sum_cF, family, regime, members}."""
    freq: Dict[Tuple[str, str], float] = {}
    form_key: Dict[Tuple[str, str], str] = {}
    for stem, entry in cmap.items():
        rec = ppa.get(stem)
        if rec is None:
            raise SystemExit(f"no Vivado result for {stem}; finish run_ppa.py first")
        f = float(rec.get("fmax_mhz", 0.0)) if rec.get("compiled") else 0.0
        for member in entry["members"]:
            freq[(member["run"], member["module"])] = f
            form_key[(member["run"], member["module"])] = entry["key"]
    table: Dict[str, Dict[str, dict]] = {}
    for run in plan["runs"]:
        summary_path = os.path.join(run["out_dir"], "holdout_summary.json")
        if not os.path.isfile(summary_path):
            continue
        summary = load_json(summary_path)[run["id"]]
        manifest = load_json(os.path.join(run["out_dir"], "fmax_manifest.json"))
        rows = {d: {"n": s["n"], "correct": s["n_correct"], "sum_cF": 0.0,
                    "family": s["family"], "regime": s["regime"], "forms": {}}
                for d, s in summary.items()}
        for module, rec in manifest.items():
            if (run["id"], module) not in freq:
                raise SystemExit(f"{run['id']}/{module} missing from candidate_map; rerun collect")
            row = rows[rec["design"]]
            row["sum_cF"] += rec["count"] * freq[(run["id"], module)]
            key = form_key[(run["id"], module)]
            row["forms"][key] = row["forms"].get(key, 0) + rec["count"]
        for d, row in rows.items():
            if sum(row["forms"].values()) != row["correct"]:
                raise SystemExit(f"{run['id']}/{d}: multiplicities do not sum to n_correct")
        table[run["id"]] = rows
    return table


def endpoints(row: dict) -> Dict[str, Optional[float]]:
    q = row["correct"] / row["n"]
    mu = row["sum_cF"] / row["correct"] if row["correct"] else None
    counts = list(row["forms"].values())
    total = sum(counts)
    support = (total * total / sum(c * c for c in counts)) if total else 0.0
    return {"q": q, "mu": mu, "F": row["sum_cF"] / row["n"], "support": support}


def stratified_bootstrap(diffs: Dict[str, float], strata: Dict[str, str],
                         seed: int = BOOTSTRAP_SEED, n: int = RESAMPLES) -> Tuple[float, float]:
    """95% percentile interval of the mean paired difference, resampling within strata."""
    groups: Dict[str, List[float]] = defaultdict(list)
    for design, value in diffs.items():
        groups[strata[design]].append(value)
    rng = random.Random(seed)
    total = len(diffs)
    means = []
    for _ in range(n):
        s = 0.0
        for values in groups.values():
            k = len(values)
            s += sum(values[rng.randrange(k)] for _ in range(k))
        means.append(s / total)
    means.sort()
    return means[int(0.025 * n)], means[int(0.975 * n) - 1]


def contrasts(table: Dict[str, Dict[str, dict]], plan: dict) -> List[dict]:
    out = []
    for run in plan["runs"]:
        if run["arm"] == "fp16" or run["id"] not in table:
            continue
        ref_id = f"{run['policy']}_fp16"
        if ref_id not in table:
            continue
        arm, ref = table[run["id"]], table[ref_id]
        designs = sorted(set(arm) & set(ref))
        strata = {d: f"{ref[d]['family']}|{ref[d]['regime']}" for d in designs}
        e_arm = {d: endpoints(arm[d]) for d in designs}
        e_ref = {d: endpoints(ref[d]) for d in designs}
        result = {"run": run["id"], "policy": run["policy"], "arm": run["arm"],
                  "n_designs": len(designs)}
        for key in ("q", "F"):
            diffs = {d: e_arm[d][key] - e_ref[d][key] for d in designs}
            lo, hi = stratified_bootstrap(diffs, strata)
            result[key] = {"ref": sum(e_ref[d][key] for d in designs) / len(designs),
                           "arm": sum(e_arm[d][key] for d in designs) / len(designs),
                           "diff": sum(diffs.values()) / len(diffs), "ci": [lo, hi],
                           "ci_unstratified": list(stratified_bootstrap(
                               diffs, {d: "all" for d in designs}))}
        both = [d for d in designs if e_arm[d]["mu"] is not None and e_ref[d]["mu"] is not None]
        if both:
            diffs = {d: e_arm[d]["mu"] - e_ref[d]["mu"] for d in both}
            lo, hi = stratified_bootstrap(diffs, {d: strata[d] for d in both})
            ref_mu = sum(e_ref[d]["mu"] for d in both) / len(both)
            diff = sum(diffs.values()) / len(both)
            result["mu"] = {"ref": ref_mu, "arm": ref_mu + diff, "diff": diff, "ci": [lo, hi],
                            "ci_unstratified": list(stratified_bootstrap(
                                diffs, {d: "all" for d in both})),
                            "relative_loss": (-diff / ref_mu) if ref_mu else None,
                            "n_designs": len(both)}
        else:
            result["mu"] = None
        shares = []
        for d in both:
            majority = max(ref[d]["forms"].items(), key=lambda kv: (kv[1], kv[0]))[0]
            shares.append(1 - arm[d]["forms"].get(majority, 0) / arm[d]["correct"])
        result["off_fp16_majority_share"] = sum(shares) / len(shares) if shares else None
        result["support"] = {
            "ref": sum(e_ref[d]["support"] for d in designs) / len(designs),
            "arm": sum(e_arm[d]["support"] for d in designs) / len(designs)}
        out.append(result)
    return out


def decide(results: List[dict]) -> Dict[str, object]:
    def meets_a(r):
        mu = r["mu"]
        return bool(mu and mu["ci"][1] < 0 and mu["relative_loss"] is not None
                    and mu["relative_loss"] >= 0.10)

    gptq = [r for r in results if r["arm"].startswith("gptq") and not r["arm"].endswith("t")]
    rtn = [r for r in results if r["arm"].startswith("rtn")]
    a_gptq = [r["run"] for r in gptq if meets_a(r)]
    a_rtn = [r["run"] for r in rtn if meets_a(r)]
    small = all(r["mu"] is None or (r["mu"]["relative_loss"] or 0) < 0.05 for r in gptq)
    if a_gptq:
        outcome = "A"
    elif a_rtn:
        outcome = "A-prime (RTN only; decide as B)"
    elif small:
        outcome = "B"
    else:
        outcome = "inconclusive"
    c = next((r for r in results if r["run"] == "stu_gptq4"), None)
    collapse = bool(c and c["q"]["arm"] < 0.5 * c["q"]["ref"])
    return {"outcome": outcome, "A_runs": a_gptq, "A_prime_runs": a_rtn,
            "C_student_gptq4_correctness_collapse": collapse}


def analyze(args: argparse.Namespace) -> None:
    plan = load_json(os.path.join(WORK, "plan.json"))
    cmap = load_json(os.path.join(args.vivado, "candidate_map.json"))
    ppa = {}
    with open(os.path.join(args.vivado, "ppa.jsonl"), encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rec = json.loads(line)
                ppa[rec["module"]] = rec
    table = design_table(plan, cmap, ppa)
    results = contrasts(table, plan)
    decision = decide(results)
    report = {"schema": "gate0_analysis/1", "resamples": RESAMPLES,
              "bootstrap_seed": BOOTSTRAP_SEED, "contrasts": results, "decision": decision,
              "per_design": {run: {d: endpoints(row) for d, row in rows.items()}
                             for run, rows in table.items()}}
    path = os.path.join(args.vivado, "gate0_analysis.json")
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, indent=1)
        handle.write("\n")

    def fmt(block, key):
        if not block:
            return "n/a"
        lo, hi = block["ci"]
        return f"{block['diff']:+8.2f} [{lo:+.2f}, {hi:+.2f}]"

    print(f"{'run':12s} {'designs':>7s}  {'dq (pp)':>24s}  {'dmu (MHz)':>26s}  {'dF (MHz)':>26s}  loss")
    for r in results:
        q = dict(r["q"], diff=100 * r["q"]["diff"], ci=[100 * x for x in r["q"]["ci"]])
        loss = r["mu"]["relative_loss"] if r["mu"] else None
        print(f"{r['run']:12s} {r['n_designs']:7d}  {fmt(q, 'q'):>24s}  {fmt(r['mu'], 'mu'):>26s}  "
              f"{fmt(r['F'], 'F'):>26s}  {'' if loss is None else f'{100 * loss:.1f}%'}")
    print(f"\ndecision: {decision}")
    print(f"report: {path}")


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="command", required=True)
    c = sub.add_parser("collect")
    c.add_argument("--out", default=os.path.join(WORK, "vivado"))
    c.add_argument("--allow-partial", action="store_true")
    c.set_defaults(func=collect)
    a = sub.add_parser("analyze")
    a.add_argument("--vivado", default=os.path.join(WORK, "vivado"))
    a.set_defaults(func=analyze)
    args = ap.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
