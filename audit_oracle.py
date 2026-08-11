#!/usr/bin/env python3
"""
audit_oracle.py  --  acceptance-criterion audit of the V2 oracle.

Re-scores ALREADY-STORED candidates (no generation, no GPU, no Vivado) under
four acceptance rules and reports where they disagree. This exists because the
paper's evaluation section is attacked on the acceptance criterion, and the
criterion has never been measured -- only asserted.

The four rules
--------------
  now       current protocol: warmup=8, latency chosen per-seed to MAXIMISE the
            match on the very trace being scored, accept if frac >= 0.999.
  exact     same, but require frac == 1.0 (no mismatched sample at all).
  warmup0   warmup=0: the post-reset startup cycles ARE compared. The current
            oracle discards the first 8 outputs on both sides, so reset and
            startup behaviour is not merely loosely checked -- it is never
            checked. This rule is the only one that can see that bug class.
  frozen    latency L* is inferred on seed 1 and then FROZEN: seed 2 must match
            at exactly L*. The current rule lets a candidate pass at L=3 on one
            seed and L=7 on another, i.e. hides state-dependent pipeline depth.

Why "exact" is expected to be a near-no-op (and why we measure it anyway):
align_score compares k = n - L - warmup samples, so at the eval length n=1024
the 0.999 rule tolerates at most ONE mismatched sample in 1016, and at the
training length n=512 it tolerates ZERO. The threshold is therefore not an
approximate-similarity score, and this run is what lets us say so with a number
instead of an argument.

Usage (sandbox, iverilog required):
    python audit_oracle.py --dirs rtl/holdout_eval_v8_* --out audit_oracle.jsonl
    python audit_oracle.py --dirs rtl/holdout_eval --limit 40 --workers 8
    python audit_oracle.py --report --out audit_oracle.jsonl
"""

import os
import re
import json
import glob
import argparse
import multiprocessing as mp

import numpy as np

import oracle

HERE = os.path.dirname(os.path.abspath(__file__))

EVAL_N = 1024          # evaluation stimulus length (matches eval_holdout)
EVAL_SEEDS = (1, 2)    # evaluation seeds (disjoint from the training seed 0)
PASS = 0.999           # the criterion under audit
MAX_LAT = 40
WARMUP = 8

# rtl/<dir>/<policy>__<design>__g<k>.sv
FNAME = re.compile(r"^(?P<policy>[^_].*?)__(?P<design>.+?)__g(?P<g>\d+)$")


def frac_at(y_dut, y_ref, L, warmup):
    """Match fraction at a SPECIFIC latency offset (no search)."""
    if y_dut is None:
        return 0.0, 0
    a = y_dut[L + warmup:]
    b = y_ref[warmup:warmup + len(a)]
    k = min(len(a), len(b))
    if k < 32:
        return 0.0, k
    return float(np.mean(a[:k] == b[:k])), k


def best_over_lat(y_dut, y_ref, warmup):
    """Reproduce align_score's best-of-41 search at a given warmup."""
    best, best_L, best_k = 0.0, -1, 0
    for L in range(MAX_LAT + 1):
        f, k = frac_at(y_dut, y_ref, L, warmup)
        if k >= 32 and f > best:
            best, best_L, best_k = f, L, k
    return best, best_L, best_k


def load_candidate(path):
    """Read a stored candidate and rename its top module back to the design
    name. run_ppa renamed each module to the filename stem so Vivado could take
    top-from-filename; oracle.run_dut requires the module to be named <design>."""
    stem = os.path.splitext(os.path.basename(path))[0]
    m = FNAME.match(stem)
    if not m:
        return None
    design = m.group("design")
    rtl = open(path, "r", errors="replace").read()
    rtl = re.sub(r"\bmodule\s+" + re.escape(stem) + r"\b",
                 "module " + design, rtl)
    return {"key": os.path.join(os.path.basename(os.path.dirname(path)), stem),
            "path": path, "policy": m.group("policy"), "design": design,
            "g": int(m.group("g")), "rtl": rtl}


def audit_one(cand):
    """Score one candidate under all four rules. Pure CPU + iverilog."""
    out = {k: cand[k] for k in ("key", "policy", "design", "g")}
    try:
        ref_fn, in_w = oracle.build_reference(cand["design"])
    except Exception as e:                       # design not in the catalog
        out["error"] = f"no_reference: {e}"
        return out

    per_seed = {}
    for seed in EVAL_SEEDS:
        stim = oracle.gen_stimulus(EVAL_N, in_w, seed)
        y_ref = ref_fn(stim)
        try:
            y_dut = oracle.run_dut(cand["rtl"], cand["design"], stim, in_w)
        except RuntimeError:                     # simulator missing -> abort loudly
            raise
        except Exception as e:
            out["error"] = f"sim: {e}"
            return out
        f8, L8, k8 = best_over_lat(y_dut, y_ref, WARMUP)
        f0, L0, k0 = best_over_lat(y_dut, y_ref, 0)
        # legacy parse: the pre-fix oracle DELETED every x/z sample instead of
        # comparing it, so its trace is exactly this one with the sentinels
        # removed. Scoring both lets the audit say whether the defect ever
        # changed a verdict on real candidates, rather than only on injected
        # faults.
        n_undef = 0 if y_dut is None else int((y_dut == oracle.X_SENTINEL).sum())
        y_leg = None if y_dut is None else y_dut[y_dut != oracle.X_SENTINEL]
        if y_leg is not None and len(y_leg) < 32:
            y_leg = None
        f_leg, _, _ = best_over_lat(y_leg, y_ref, WARMUP)
        per_seed[seed] = {"compiled": y_dut is not None,
                          "frac_w8": f8, "lat_w8": L8, "k_w8": k8,
                          "frac_w0": f0, "lat_w0": L0, "k_w0": k0,
                          "n_undef": n_undef, "frac_legacy": f_leg,
                          "_dut": y_dut, "_ref": y_ref}

    s1, s2 = per_seed[EVAL_SEEDS[0]], per_seed[EVAL_SEEDS[1]]

    # frozen-latency rule: infer L* on seed 1, enforce it on seed 2
    Lstar = s1["lat_w8"]
    f_frozen, _ = (frac_at(s2["_dut"], s2["_ref"], Lstar, WARMUP)
                   if Lstar >= 0 else (0.0, 0))

    for s in per_seed.values():
        s.pop("_dut", None)
        s.pop("_ref", None)

    out["seeds"] = {str(k): v for k, v in per_seed.items()}
    out["lat_star"] = Lstar
    out["frac_frozen_seed2"] = f_frozen
    out["lat_consistent"] = bool(s1["lat_w8"] == s2["lat_w8"] and s1["lat_w8"] >= 0)

    # the four acceptance decisions (a candidate must pass on BOTH seeds)
    out["n_undef"] = max(s1["n_undef"], s2["n_undef"])
    out["accept_legacy"] = bool(min(s1["frac_legacy"], s2["frac_legacy"]) >= PASS)
    out["accept_now"] = bool(min(s1["frac_w8"], s2["frac_w8"]) >= PASS)
    out["accept_exact"] = bool(min(s1["frac_w8"], s2["frac_w8"]) >= 1.0)
    out["accept_warmup0"] = bool(min(s1["frac_w0"], s2["frac_w0"]) >= PASS)
    out["accept_frozen"] = bool(s1["frac_w8"] >= PASS and f_frozen >= PASS)
    return out


def run_audit(args):
    paths = []
    for d in args.dirs:
        paths.extend(sorted(glob.glob(os.path.join(d, "*.sv"))))
    cands = [c for c in (load_candidate(p) for p in paths) if c]
    if args.limit:
        cands = cands[:args.limit]

    done = set()
    if os.path.exists(args.out) and not args.overwrite:
        for line in open(args.out):
            try:
                done.add(json.loads(line)["key"])
            except Exception:
                pass
    todo = [c for c in cands if c["key"] not in done]
    print(f"{len(cands)} candidates found, {len(done)} already audited, "
          f"{len(todo)} to do")
    if not todo:
        return

    workers = args.workers or max(1, (os.cpu_count() or 2) - 1)
    with open(args.out, "a") as fh, mp.Pool(workers) as pool:
        for i, rec in enumerate(pool.imap_unordered(audit_one, todo, 1), 1):
            fh.write(json.dumps(rec) + "\n")
            fh.flush()
            if i % 25 == 0 or i == len(todo):
                print(f"  {i}/{len(todo)}", flush=True)


def run_report(args):
    recs = [json.loads(l) for l in open(args.out)]
    ok = [r for r in recs if "error" not in r]
    print(f"\naudited {len(recs)} candidates ({len(recs) - len(ok)} errored)\n")

    now = [r for r in ok if r["accept_now"]]
    print(f"accepted by the CURRENT rule: {len(now)}/{len(ok)}\n")

    # undefined-output accounting (the x/z parse defect)
    und = [r for r in ok if r.get("n_undef", 0)]
    if any("accept_legacy" in r for r in ok):
        flip_in = [r for r in ok if r.get("accept_legacy") and not r["accept_now"]]
        flip_out = [r for r in ok if r["accept_now"] and not r.get("accept_legacy")]
        print(f"candidates emitting x/z on some cycle: {len(und)}/{len(ok)}")
        print(f"  accepted by the OLD (x/z-deleting) parse but not now: "
              f"{len(flip_in)}   <- false positives the defect could hide")
        print(f"  accepted now but not by the old parse:                "
              f"{len(flip_out)}")
        for r in flip_in[:10]:
            print(f"    + {r['key']:52s} undef={r['n_undef']}")
        print()
    print("Of those accepted now, how many survive each stricter rule?")
    for rule, label in [("accept_exact", "exact equality (frac == 1.0)"),
                        ("accept_warmup0", "warmup=0 (reset window compared)"),
                        ("accept_frozen", "frozen latency across seeds")]:
        surv = sum(1 for r in now if r[rule])
        lost = len(now) - surv
        pct = 100.0 * lost / len(now) if now else 0.0
        print(f"  {label:38s} {surv:5d} survive, {lost:5d} lost ({pct:.1f}%)")

    incons = [r for r in now if not r["lat_consistent"]]
    print(f"\nlatency INCONSISTENT across seeds (accepted anyway): "
          f"{len(incons)}/{len(now)}")
    for r in incons[:10]:
        s = r["seeds"]
        print(f"    {r['key']:52s} L={s['1']['lat_w8']} vs {s['2']['lat_w8']}")

    # who loses candidates when the reset window is compared
    print("\nwarmup=0 losses by family/policy:")
    by = {}
    for r in now:
        fam = re.match(r"[a-z]+", r["design"]).group(0)
        k = (r["policy"], fam)
        by.setdefault(k, [0, 0])
        by[k][0] += 1
        by[k][1] += 0 if r["accept_warmup0"] else 1
    for (pol, fam), (tot, lost) in sorted(by.items()):
        if lost:
            print(f"    {pol:10s} {fam:6s} {lost:4d}/{tot:4d} lost "
                  f"({100.0 * lost / tot:.1f}%)")

    near = [r for r in ok
            if 0.0 < min(r['seeds']['1']['frac_w8'],
                         r['seeds']['2']['frac_w8']) < PASS]
    print(f"\nnear-misses (0 < frac < {PASS} on some seed): {len(near)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dirs", nargs="*", default=[
        os.path.join(HERE, "rtl", "holdout_eval_v8_firfirr"),
        os.path.join(HERE, "rtl", "holdout_eval_v8_poly"),
        os.path.join(HERE, "rtl", "holdout_eval_v8_iirmed"),
    ])
    ap.add_argument("--out", default=os.path.join(HERE, "audit_oracle.jsonl"))
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int, default=0)
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args()

    if args.report:
        run_report(args)
    else:
        run_audit(args)
        run_report(args)


if __name__ == "__main__":
    main()
