#!/usr/bin/env python3
"""
regen_tables.py  -  THE single source for every headline number in the paper.

Every table, every percentage, every claim in the manuscript is produced here
and nowhere else. It also emits `claims.json`, a machine-readable record of each
number with the artifact it came from, so prose can be checked against
computation instead of against memory.

WHY THIS EXISTS. Six numbers in one week were wrong in prose while the scripts
that produced them were right. `analyze_bestofn.py` had already printed its own
withdrawal; the prose was never updated. A best-of-48 claim computed on a
superseded 22-design set was reintroduced from memory. A +252% figure from the
old 3-family suite was quoted as if it were the frozen 5-family result, paired
with the favourable half of a two-part correctness finding. None of these were
bad experiments. All of them were sentences that drifted from artifacts.

So: no number reaches the manuscript unless it has a key in claims.json.

PRIMARY ENDPOINT (penalized, equal-sample):
    per (policy, design):  sum over distinct candidates of (multiplicity x real
    Fmax), divided by n -- the TOTAL samples drawn for that design.
    A sample that was incorrect, or whose candidate failed synthesis, scores
    ZERO. This is the honest cost accounting: a policy that emits one brilliant
    design and 47 broken ones did not do well, and a conditional-on-correct mean
    would hide exactly that. Conditional means and correctness rates are
    reported too, as SECONDARY, never as the headline.

UNCERTAINTY: paired design-level bootstrap, 95%, designs resampled within
regime, identical resamples across policies. Design is the unit of
independence; 48 samples per design reduce within-design noise, they do not
create 1440 observations.

    python regen_tables.py --out claims.json
"""

import os
import json
import glob
import argparse
import collections

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))

# The FROZEN 30-design held-out set, as three committed evaluation directories.
# Asserted below: exactly 30 distinct designs, no more, no fewer.
EVAL_DIRS = ["rtl/holdout_eval_v8_firfirr", "rtl/holdout_eval_v8_poly",
             "rtl/holdout_eval_v8_iirmed"]
N_DESIGNS = 30
N_BOOT = 100_000
CI = 0.95
BOOT_SEED = 20260813


def family_of(d):
    for f in ("firr", "fir", "poly", "iir", "med", "cordic"):
        if d.startswith(f):
            return f
    return "other"


def load(dirs):
    """-> {(policy, design): {equal, cond, correct_rate, n, regime, family}}"""
    agg = collections.defaultdict(
        lambda: {"sum": 0.0, "ok": 0, "correct": 0, "n": None,
                 "regime": None, "src": set()})
    for d in dirs:
        dd = os.path.join(HERE, d)
        mani = json.load(open(os.path.join(dd, "fmax_manifest.json")))
        real = {}
        p = os.path.join(dd, "ppa.jsonl")
        for line in open(p):
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r.get("compiled") and r.get("fmax_mhz") is not None:
                real[r["module"]] = float(r["fmax_mhz"])
        for mod, info in mani.items():
            key = (info["policy"], info["design"])
            a = agg[key]
            c = int(info.get("count", 1))
            a["correct"] += c              # in the manifest => oracle-correct
            a["n"] = int(info.get("n", 48))
            a["regime"] = info.get("regime")
            a["src"].add(d)
            if mod in real:                # synthesised successfully
                a["sum"] += c * real[mod]
                a["ok"] += c
    out = {}
    for (pol, des), a in agg.items():
        n = a["n"]
        out[(pol, des)] = {
            "equal": a["sum"] / n,
            "cond": (a["sum"] / a["ok"]) if a["ok"] else 0.0,
            "correct_rate": a["correct"] / n,
            "n": n, "regime": a["regime"], "family": family_of(des),
            "src": sorted(a["src"])}
    return out


def boot(diff, rng):
    """Paired bootstrap over designs. `diff` is one value per design."""
    diff = np.asarray(diff, float)
    idx = rng.integers(0, len(diff), (N_BOOT, len(diff)))
    stats = diff[idx].mean(axis=1)
    return (float(diff.mean()),
            float(np.quantile(stats, (1 - CI) / 2)),
            float(np.quantile(stats, 1 - (1 - CI) / 2)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dirs", nargs="*", default=EVAL_DIRS)
    ap.add_argument("--out", default=os.path.join(HERE, "claims.json"))
    args = ap.parse_args()

    data = load(args.dirs)
    designs = sorted({d for (_p, d) in data})
    if len(designs) != N_DESIGNS:
        raise SystemExit(f"expected exactly {N_DESIGNS} designs, found "
                         f"{len(designs)}: {designs}\nThis guard exists because "
                         f"a superseded 22-design set was once analysed as if it "
                         f"were the frozen one.")
    regime = {d: data[("sft", d)]["regime"] for d in designs}
    # `bestof8` is EXCLUDED from the equal-sample table. It is a SELECTION
    # procedure over 8 samples, not a policy sampled n times, so dividing its
    # total by n=48 is not the same quantity and would understate it by ~6x.
    # Best-of-N belongs to analyze_bestofn.py, which models it in closed form.
    policies = [p for p in sorted({p for (p, _d) in data}) if p != "bestof8"]
    print(f"designs: {len(designs)}   policies: {policies}")
    print("bestof8 EXCLUDED here by design -- see analyze_bestofn.py")
    print(f"regimes: {collections.Counter(regime.values())}\n")

    claims = {"_meta": {"script": "regen_tables.py", "inputs": args.dirs,
                        "n_designs": len(designs), "n_boot": N_BOOT,
                        "ci": CI, "boot_seed": BOOT_SEED,
                        "primary_endpoint":
                        "penalized equal-sample Fmax: sum(multiplicity x real "
                        "Fmax)/n, incorrect and synthesis-failed samples = 0",
                        "unit_of_independence": "design"}}

    def put(key, value, note, **extra):
        claims[key] = dict(value=value, note=note, **extra)

    # ---- headline table -------------------------------------------------
    print(f"{'regime':14s} {'n':>3s} " +
          " ".join(f"{p:>10s}" for p in policies))
    print("-" * 64)
    for rg in ("interp", "extrap", "ALL"):
        ds = [d for d in designs if rg == "ALL" or regime[d] == rg]
        row = []
        for p in policies:
            vals = [data[(p, d)]["equal"] for d in ds if (p, d) in data]
            m = float(np.mean(vals)) if vals else float("nan")
            row.append(m)
            put(f"equal_{p}_{rg}", round(m, 1),
                f"penalized equal-sample mean Fmax, {p}, {rg}",
                unit="MHz", n_designs=len(vals))
        print(f"{rg:14s} {len(ds):3d} " + " ".join(f"{v:10.1f}" for v in row))

    # ---- SFT -> GRPO, the primary comparison ----------------------------
    print(f"\n{'regime':14s} {'gain':>9s} {'95% CI':>20s} {'improved':>10s}")
    print("-" * 60)
    rng = np.random.default_rng(BOOT_SEED)
    for rg in ("interp", "extrap", "ALL"):
        ds = [d for d in designs if rg == "ALL" or regime[d] == rg]
        diff = [data[("grpo", d)]["equal"] - data[("sft", d)]["equal"] for d in ds]
        m, lo, hi = boot(diff, rng)
        imp = sum(1 for x in diff if x > 0)
        print(f"{rg:14s} {m:+9.1f} [{lo:+8.1f}, {hi:+8.1f}]  {imp:4d}/{len(ds):<4d}")
        put(f"gain_grpo_vs_sft_{rg}", round(m, 1),
            f"mean paired design-level gain, penalized equal-sample, {rg}",
            unit="MHz", ci95=[round(lo, 1), round(hi, 1)],
            designs_improved=imp, n_designs=len(ds))

    # ---- secondary: correctness and conditional means --------------------
    print(f"\n{'regime':14s} {'policy':8s} {'correct':>8s} {'cond MHz':>9s}")
    print("-" * 46)
    for rg in ("interp", "extrap"):
        ds = [d for d in designs if regime[d] == rg]
        for p in ("sft", "grpo"):
            cr = float(np.mean([data[(p, d)]["correct_rate"] for d in ds]))
            cd = float(np.mean([data[(p, d)]["cond"] for d in ds]))
            print(f"{rg:14s} {p:8s} {100*cr:7.1f}% {cd:9.1f}")
            put(f"correct_{p}_{rg}", round(100 * cr, 1),
                f"mean per-design correctness rate, {p}, {rg}", unit="%")
            put(f"cond_{p}_{rg}", round(cd, 1),
                f"conditional-on-correct mean Fmax (SECONDARY), {p}, {rg}",
                unit="MHz")

    # ---- per-design table, for the appendix and for auditing -------------
    per = {}
    for d in designs:
        per[d] = {"regime": regime[d], "family": family_of(d),
                  **{p: {"equal": round(data[(p, d)]["equal"], 1),
                         "cond": round(data[(p, d)]["cond"], 1),
                         "correct": round(data[(p, d)]["correct_rate"], 3)}
                     for p in policies if (p, d) in data}}
    claims["_per_design"] = per

    json.dump(claims, open(args.out, "w"), indent=1, sort_keys=True)
    n = sum(1 for k in claims if not k.startswith("_"))
    print(f"\nwrote {args.out}  ({n} named claims)")
    print("\nEvery number above now has a key. Nothing enters the manuscript "
          "without one.")


if __name__ == "__main__":
    main()
