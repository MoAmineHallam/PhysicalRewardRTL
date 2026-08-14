#!/usr/bin/env python3
"""
analyze_sealed.py  -  the FROZEN analysis of the sealed evaluation.

Written and hashed BEFORE the sealed split was generated, which is the only
reason it means anything. Every choice a person could otherwise make after
seeing the numbers is already made here: how a failed sample is scored, how
duplicates are weighted, how designs are aggregated, how the interval is built,
and which outcome label the result earns.

PRIMARY ENDPOINT (one number, decided in advance)
    per design: EQUAL-SAMPLE mean Fmax
        sum over distinct correct candidates of (multiplicity x real Fmax),
        divided by the TOTAL number of samples drawn for that design.
    Samples that are incorrect, that error in the oracle, that fail synthesis or
    that time out all contribute ZERO. This is the honest cost accounting: an
    arm that produces one brilliant design and 23 broken ones did not do well,
    and conditional-on-correct means would hide that. The conditional mean is
    reported too, as a secondary, never as the headline.

    effect = mean over designs of (arm - SFT), designs weighted EQUALLY.

DUPLICATES
    Synthesised once, but weighted by how often the policy actually produced
    them. Deduplicating for the endpoint would silently reward a policy that
    concentrates on one output; that concentration is a real property and
    multiplicity is how it enters the number.

UNCERTAINTY
    95% paired bootstrap, 100,000 replicates, resampling DESIGNS within each
    family x regime stratum, with the SAME resampled design indices applied to
    every arm. Design is the unit of independence -- 24 samples per design
    reduce within-design noise but do not create 480 independent observations.
    Training seeds are averaged within design for the combined interval and are
    ALSO reported separately; they are never pooled as if they were independent.

WHAT THIS SCRIPT WILL NOT DO
    It will not drop a design, re-weight a family, switch endpoint, or add a
    seed. If the result is ambiguous it prints the ambiguous label. The taxonomy
    has a name for every outcome including the boring ones, so there is nothing
    to be gained by reaching past it.

    python analyze_sealed.py --sft rtl/sealed_sft \\
        --arm rf=rtl/sealed_rf_s1,rtl/sealed_rf_s2 \\
        --arm mlp=rtl/sealed_mlp_s1 \\
        --arm correctness=rtl/sealed_corr_s1,rtl/sealed_corr_s2 \\
        --out sealed_results.json
"""

import os
import json
import argparse
import collections

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))

# ---- frozen analysis constants ------------------------------------------
N_BOOT = 100_000
CI = 0.95
BOOT_SEED = 20260813          # same seed as the split; declared, not tuned
SAMPLES_PER_DESIGN = 24       # per training seed
RETENTION_THRESHOLD = 0.50    # "high retention" modifier, not a success gate
MATERIAL_MHZ, MATERIAL_FRAC = 5.0, 0.02       # max(5 MHz, 2%)


def material(a, b):
    return abs(a - b) > max(MATERIAL_MHZ, MATERIAL_FRAC * max(abs(a), abs(b)))


def load_dir(d, samples_per_design=SAMPLES_PER_DESIGN):
    """-> {design: {"equal": x, "cond": y, "n_ok": k, "n_samples": n}}.

    Reads fmax_manifest.json (mod -> {design, count, ...}) and ppa.jsonl
    (module -> compiled, fmax_mhz). A candidate present in the manifest but
    absent from or failed in ppa.jsonl scores ZERO -- a design that could not be
    implemented is not a fast design.
    """
    mani = json.load(open(os.path.join(d, "fmax_manifest.json")))
    real = {}
    p = os.path.join(d, "ppa.jsonl")
    if os.path.exists(p):
        for line in open(p):
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r.get("compiled") and r.get("fmax_mhz") is not None:
                real[r["module"]] = float(r["fmax_mhz"])
    agg = collections.defaultdict(lambda: {"sum": 0.0, "ok": 0, "cnt": 0,
                                           "n_samples": None})
    items = mani.items() if isinstance(mani, dict) else [
        (r["module"], r) for r in mani]
    for mod, info in items:
        des = info["design"]
        c = int(info.get("count", 1))
        a = agg[des]
        a["cnt"] += c
        if mod in real:
            a["sum"] += c * real[mod]
            a["ok"] += c
        if info.get("n_samples"):
            a["n_samples"] = int(info["n_samples"])
    out = {}
    for des, a in agg.items():
        n = a["n_samples"] or samples_per_design
        out[des] = {"equal": a["sum"] / n,
                    "cond": (a["sum"] / a["ok"]) if a["ok"] else 0.0,
                    "n_ok": a["ok"], "n_cand": a["cnt"], "n_samples": n,
                    "correct_rate": a["cnt"] / n}
    return out


def load_arm(dirs):
    """Average the per-seed equal-sample values within each design."""
    per_seed = [load_dir(d) for d in dirs]
    designs = sorted(set().union(*[set(s) for s in per_seed])) if per_seed else []
    comb = {}
    for des in designs:
        vals = [s[des] for s in per_seed if des in s]
        comb[des] = {
            "equal": float(np.mean([v["equal"] for v in vals])),
            "cond": float(np.mean([v["cond"] for v in vals])),
            "correct_rate": float(np.mean([v["correct_rate"] for v in vals])),
            "n_seeds": len(vals)}
    return comb, per_seed


def strata_of(designs, sealed):
    by = {d["design"]: (d["family"], d["regime"]) for d in sealed["designs"]}
    return [by.get(d, ("unknown", "unknown")) for d in designs]


def boot_ci(diff, strata, rng):
    """Paired stratified bootstrap over DESIGNS. `diff` is per-design."""
    diff = np.asarray(diff, dtype=float)
    idx_by = collections.defaultdict(list)
    for i, s in enumerate(strata):
        idx_by[s].append(i)
    groups = [np.asarray(v) for v in idx_by.values()]
    stats = np.empty(N_BOOT)
    for b in range(N_BOOT):
        pick = np.concatenate([g[rng.integers(0, len(g), len(g))]
                               for g in groups])
        stats[b] = diff[pick].mean()
    lo = float(np.quantile(stats, (1 - CI) / 2))
    hi = float(np.quantile(stats, 1 - (1 - CI) / 2))
    return float(diff.mean()), lo, hi


def regime_report(name, arm, sft, designs, sealed, rng):
    out = {}
    for regime in ("interp", "extrap", "all"):
        ds = [d for d in designs
              if regime == "all" or strata_of([d], sealed)[0][1] == regime]
        if not ds:
            continue
        diff = [arm[d]["equal"] - sft[d]["equal"] for d in ds]
        mean, lo, hi = boot_ci(diff, strata_of(ds, sealed), rng)
        out[regime] = {"n_designs": len(ds), "mean_diff": mean,
                       "ci_lo": lo, "ci_hi": hi,
                       "excludes_zero": bool(lo > 0 or hi < 0),
                       "arm_equal": float(np.mean([arm[d]["equal"] for d in ds])),
                       "sft_equal": float(np.mean([sft[d]["equal"] for d in ds])),
                       "arm_correct": float(np.mean([arm[d]["correct_rate"]
                                                     for d in ds])),
                       "sft_correct": float(np.mean([sft[d]["correct_rate"]
                                                     for d in ds]))}
    return out


def classify(rf_report, per_seed_signs, gate_ok, resolved_frac, retention,
             late_divergence):
    """The preregistered outcome taxonomy. Exactly one label."""
    if not gate_ok:
        return ("invalid_repair",
                "prospective invariance / canonical-compilation / semantic gate "
                "failed; the arm is not a valid instance of the method")
    if resolved_frac is not None and resolved_frac < 0.20:
        return ("reward_resolution_failure",
                f"only {100*resolved_frac:.1f}% of eligible training groups were "
                f"resolved by the reward (<20%): the reward supplied almost no "
                f"gradient, so the arm tests nothing about alignment")
    signs = [s for s in per_seed_signs if s is not None]
    if len(signs) > 1 and len(set(np.sign(signs))) > 1:
        return ("seed_unstable",
                "the two training seeds disagree in the SIGN of the effect")
    interp = rf_report.get("interp", {})
    extrap = rf_report.get("extrap", {})
    both_pos = interp.get("mean_diff", 0) > 0 and extrap.get("mean_diff", 0) > 0
    both_ci = interp.get("excludes_zero") and extrap.get("excludes_zero")
    if both_pos and both_ci and not late_divergence:
        lab = "full_two_regime_repair"
        why = "improves over SFT in both regimes with CIs excluding zero"
        if retention is not None:
            why += (f"; retention {100*retention:.0f}% "
                    f"({'high' if retention >= RETENTION_THRESHOLD else 'low'})")
        return lab, why
    if both_pos and not both_ci:
        return ("directional_but_imprecise",
                "both regimes improve but at least one CI includes zero")
    one = (interp.get("mean_diff", 0) > 0) != (extrap.get("mean_diff", 0) > 0)
    if one:
        good = "interp" if interp.get("mean_diff", 0) > 0 else "extrap"
        return ("regime_limited", f"stable improvement in {good} only")
    if late_divergence:
        return ("reward_misalignment",
                "reward rose from the mid checkpoint to the endpoint while real "
                "equal-sample Fmax fell materially")
    return ("stable_null",
            "valid and resolved reward, no divergence, but no material real "
            "improvement")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sealed", default=os.path.join(HERE, "sealed_split.json"))
    ap.add_argument("--sft", required=True)
    ap.add_argument("--arm", action="append", default=[],
                    help="name=dir[,dir2] (dir2 = second training seed)")
    ap.add_argument("--primary", default="rf",
                    help="which arm carries the preregistered hypothesis")
    ap.add_argument("--mid", default="",
                    help="name=dir for the primary arm's update-138 checkpoint "
                         "(late-divergence test)")
    ap.add_argument("--mid-reward", type=float, default=None,
                    help="mean predicted reward at the mid checkpoint")
    ap.add_argument("--end-reward", type=float, default=None,
                    help="mean predicted reward at the endpoint checkpoint")
    ap.add_argument("--resolved-frac", type=float, default=None,
                    help="fraction of eligible training groups the reward "
                         "resolved (from the group log; Check B)")
    ap.add_argument("--gate-failed", action="store_true",
                    help="set if the pre-open mutation contract failed")
    ap.add_argument("--out", default=os.path.join(HERE, "sealed_results.json"))
    args = ap.parse_args()

    sealed = json.load(open(args.sealed))
    rng = np.random.default_rng(BOOT_SEED)

    sft, sft_seeds = load_arm([args.sft])
    arms = {}
    for spec in args.arm:
        name, _, dirs = spec.partition("=")
        arms[name] = load_arm([d for d in dirs.split(",") if d])

    designs = sorted(d["design"] for d in sealed["designs"])
    missing = [d for d in designs if d not in sft]
    if missing:
        print(f"WARNING: {len(missing)} sealed designs missing from the SFT "
              f"arm: {missing}\nThey are EXCLUDED from every arm so the "
              f"comparison stays paired. Report this exclusion.")
    designs = [d for d in designs
               if d in sft and all(d in a[0] for a in arms.values())]
    print(f"sealed designs analysed: {len(designs)} / {len(sealed['designs'])}")

    report = {}
    for name, (arm, seeds) in arms.items():
        rep = regime_report(name, arm, sft, designs, sealed, rng)
        per_seed = []
        for s in seeds:
            ds = [d for d in designs if d in s]
            per_seed.append(float(np.mean([s[d]["equal"] - sft[d]["equal"]
                                           for d in ds])) if ds else None)
        rep["_per_seed_mean_diff"] = per_seed
        report[name] = rep
        print(f"\n=== {name} ===")
        for rg in ("interp", "extrap", "all"):
            if rg not in rep:
                continue
            r = rep[rg]
            print(f"  {rg:7s} n={r['n_designs']:2d}  SFT {r['sft_equal']:6.1f} "
                  f"-> {r['arm_equal']:6.1f} MHz   diff {r['mean_diff']:+6.1f} "
                  f"[{r['ci_lo']:+.1f}, {r['ci_hi']:+.1f}]"
                  f"{'  *' if r['excludes_zero'] else ''}")
            print(f"          correctness {r['sft_correct']:.3f} -> "
                  f"{r['arm_correct']:.3f}")
        print(f"  per training seed, mean diff: "
              f"{['%.1f' % v if v is not None else 'n/a' for v in per_seed]}")

    # ---- retention and divergence, then the label ------------------------
    retention = None
    prim = report.get(args.primary)
    mlp = report.get("mlp")
    if prim and mlp:
        num = prim.get("all", {}).get("mean_diff")
        den = mlp.get("all", {}).get("mean_diff")
        if den is not None and den > 0 and num is not None:
            retention = num / den
        else:
            print("\nretention: NOT APPLICABLE (the original-MLP arm did not "
                  "improve on the sealed split, so there is no gain to retain)")

    late = False
    if args.mid_reward is not None and args.end_reward is not None:
        mid_arm = None
        if args.mid:
            _n, _, md = args.mid.partition("=")
            mid_arm, _ = load_arm([md])
        if mid_arm:
            ds = [d for d in designs if d in mid_arm]
            mid_f = float(np.mean([mid_arm[d]["equal"] for d in ds]))
            end_f = float(np.mean([arms[args.primary][0][d]["equal"]
                                   for d in ds]))
            late = (material(args.end_reward, args.mid_reward)
                    and args.end_reward > args.mid_reward
                    and material(end_f, mid_f) and end_f < mid_f)
            print(f"\nlate divergence: reward {args.mid_reward:.1f} -> "
                  f"{args.end_reward:.1f}, real equal-sample {mid_f:.1f} -> "
                  f"{end_f:.1f}  => {late}")
    else:
        print("\nlate divergence: NOT MEASURED (no mid-checkpoint evaluation). "
              "The weaker endpoint-only statement is the most that may be "
              "claimed: whether reward and reality disagree in sign at the "
              "endpoint.")

    label = why = None
    if prim:
        label, why = classify(prim, prim["_per_seed_mean_diff"],
                              not args.gate_failed, args.resolved_frac,
                              retention, late)
        print(f"\nPREREGISTERED OUTCOME: {label}\n  {why}")

    json.dump({"n_designs": len(designs), "designs": designs,
               "bootstrap": {"n": N_BOOT, "ci": CI, "seed": BOOT_SEED,
                             "strata": "family x regime, designs resampled, "
                                       "identical resamples across arms"},
               "sft": sft, "arms": {k: v[0] for k, v in arms.items()},
               "report": report, "retention": retention,
               "late_divergence": late, "outcome": label, "outcome_why": why},
              open(args.out, "w"), indent=1)
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
