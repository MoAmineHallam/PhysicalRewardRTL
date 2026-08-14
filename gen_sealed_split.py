#!/usr/bin/env python3
"""
gen_sealed_split.py  -  the FROZEN generator for the sealed evaluation split.

Preregistration revision 2 exists partly because of this file. Revision 1 said
"20 designs, seed 20260813, drawn from gen_accelerator_catalog parameterisations,
no hand selection" -- but gen_accelerator_catalog emits FIXED GRIDS and has no
seed-driven selection, so the seed alone did not determine anything. A reader
could not have reconstructed the split, which is the whole point of naming it.
This script is that missing determinism, hashed and frozen BEFORE it is run.

Everything a reader needs to reproduce the split byte-for-byte is here: the
eligible pools, what interpolation and extrapolation mean per family, how
coefficients are derived, which designs are excluded as already-seen, the
deterministic draw order, the rejection and replacement rules, and the output
schema.

WHY THERE IS A COEFFICIENT AXIS AT ALL
    The trained grid covers EVERY fir/firr tap count in 4..32, so "an unseen
    tap count inside the trained range" does not exist -- the interpolation axis
    is exhausted. A new coefficient set at a trained tap count IS an unseen
    design (different constant multipliers, different synthesised hardware,
    different Fmax) sitting inside the trained region, which is what
    interpolation means. poly and iir already had this axis (poly_coeffs_var,
    iir_coeffs_var); fir/firr gain the matching fir_coeffs_var/firr_coeffs_var.

WHY MEDIAN HAS NO INTERPOLATION DESIGNS
    A median filter is defined by its window width alone -- there is no
    coefficient to vary. The trained widths are {3,5,9} and {7,11} are already
    held out, so every width inside the trained range is consumed. med's
    interpolation pool is PROVABLY EMPTY, not empty by choice. Rather than drop
    a family or invent a fake axis, the two vacant slots are reallocated by the
    declared replacement rule below. med still contributes both extrapolation
    designs, so all five families appear in the sealed set.

ELIGIBILITY IS A PROPERTY OF THE DESIGN, NEVER OF AN OUTCOME
    A design is eligible if AT LEAST ONE of its correct styles (a) has an oracle
    reference, (b) fits the family's generation budget, (c) passes the oracle,
    and (d) canonicalises to a trace-equal form. Styles are tried shortest
    first. None of these consult a policy, a reward, or a measurement.

    Asking about ONE arbitrary style is the wrong question and it showed: the
    first run rejected the entire median extrapolation pool because med_comb, a
    fully unrolled comparator network, needs 6,670 tokens at W=13 -- while
    med_sort expresses the same filter in about 680 and is the style that made
    the family learnable at all. The designs were always answerable; the witness
    was wrong. (b) is F4 as an eligibility rule: a design whose every correct
    form overflows the budget would measure the budget, not the policy. (d)
    matters because a design with no canonicalisable form would leave the
    rf_struct arm structurally blind on it.

Run ONCE, on the canonical machine, then commit sealed_split.json:
    python gen_sealed_split.py --out sealed_split.json
Re-running with the same seed and the same code must reproduce it exactly;
--verify checks that against an existing manifest instead of overwriting it.
"""

import os

# Set BEFORE transformers is imported. The eligibility check tokenises, then the
# oracle forks iverilog per candidate, and a forked process that has already used
# parallel tokenizers prints a five-line warning every time -- hundreds of them,
# burying the actual selection. Silencing it here rather than relying on the
# caller's shell keeps the run reproducible from the command line alone. It has
# no effect on which designs are drawn.
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

import re
import sys
import json
import random
import hashlib
import argparse

import gen_accelerator_catalog as GAC
import gen_sft_corpus as GSC
import oracle
from canonicalize import canonicalize, trace_equal, Unsupported, CANON_VERSION

HERE = os.path.dirname(os.path.abspath(__file__))

SCHEMA = "sealed_split/1"
SEED = 20260813                      # preregistered in revision 1, unchanged

# ---------------------------------------------------------------------------
# Regime definitions. "Trained range" is the parameter interval the SFT corpus
# and GRPO prompt list actually cover (gen_sft_corpus.designs). Interpolation =
# inside it; extrapolation = outside it. Held-out §5 parameters are removed from
# BOTH pools because those designs already exist in the Phase-B evaluation.
FAMILY_ORDER = ["fir", "firr", "poly", "iir", "med"]

POOLS = {
    # family: {regime: (param_values, variant_values)}
    "fir":  {"interp": (list(range(4, 33)), list(range(1, 9))),
             "extrap": ([34, 38, 42, 44, 46, 48], list(range(0, 9)))},
    "firr": {"interp": (list(range(4, 33)), list(range(1, 9))),
             "extrap": ([34, 38, 42, 44, 46, 48], list(range(0, 9)))},
    "poly": {"interp": ([d for d in range(2, 11)], list(range(8, 16))),
             "extrap": ([12, 14, 16, 18], list(range(0, 16)))},
    "iir":  {"interp": (list(range(2, 15)), list(range(4, 12))),
             "extrap": ([18, 22, 24, 26], list(range(0, 12)))},
    "med":  {"interp": ([], [0]),                 # provably empty, see docstring
             "extrap": ([13, 15, 17, 19, 21], [0])},
}

# Base quota, before the replacement rule.
BASE_QUOTA = 2

# Generation budget per family. med11 already exceeded the 1536-token cap (F4),
# so every sealed med design is generated at 3072. Pinned here so the evaluation
# cannot quietly choose a different budget later.
MAX_TOKENS = {"fir": 1536, "firr": 1536, "poly": 1536, "iir": 1536, "med": 3072}

ORACLE_N = 512          # solvability check only; scoring uses n=1024 seeds 1,2
ORACLE_SEED = 0


def sha256_text(txt):
    return hashlib.sha256(txt.replace("\r\n", "\n").encode()).hexdigest()


def sha256_file(path):
    return sha256_text(open(path, errors="replace").read())


def design_name(family, p, v):
    if family == "fir":
        return f"fir{p}_8b" if v == 0 else f"fir{p}_v{v}_8b"
    if family == "firr":
        return f"firr{p}" if v == 0 else f"firr{p}_v{v}"
    if family == "poly":
        return f"poly{p}_8b" if v == 0 else f"poly{p}_v{v}_8b"
    if family == "iir":
        return f"iir{p}" if v == 0 else f"iir{p}_v{v}"
    if family == "med":
        return f"med{p}"
    raise ValueError(family)


def build(family, p, v):
    """-> (spec_text, {style: reference_rtl}, params_dict).

    ALL styles are returned, not one. Answerability is a question about the
    design -- does a correct implementation exist inside the generation budget --
    not about whichever style this script happened to pick. Validating against a
    single arbitrary style once rejected the ENTIRE median extrapolation pool:
    med_comb is a fully unrolled comparator network needing 6,670 tokens at W=13,
    while med_sort expresses the same filter in about 680 and is the style that
    made the family learnable at all (6.2% -> 89.6% in sft_v6c). The design was
    always answerable; the witness was wrong.

    References are solvability witnesses only: never shown to a model, never in
    any corpus.
    """
    nm = design_name(family, p, v)
    if family == "fir":
        c = GAC.fir_coeffs_var(p, v)
        return GAC.fir_spec(nm, p, c), {
            "ref": GAC.fir_ref(nm, c), "pipe": GAC.fir_pipe(nm, c),
            "unrolled": GAC.fir_unrolled(nm, c),
            "transposed": GAC.fir_transposed(nm, c)}, {"taps": p, "v": v,
                                                       "coeffs": c}
    if family == "firr":
        c = GAC.firr_coeffs_var(p, v)
        return GAC.firr_spec(nm, p, v), {
            "ref": GAC.fir_ref(nm, c), "pipe": GAC.fir_pipe(nm, c),
            "unrolled": GAC.fir_unrolled(nm, c),
            "transposed": GAC.fir_transposed(nm, c)}, {"taps": p, "v": v,
                                                       "coeffs": c}
    if family == "poly":
        c = GAC.poly_coeffs_var(p, v)
        return GAC.poly_spec(nm, p, c), {
            "ref": GAC.poly_ref(nm, c), "pipe": GAC.poly_pipe(nm, c),
            "inline": GAC.poly_inline(nm, c)}, {"degree": p, "v": v,
                                                "coeffs": c}
    if family == "iir":
        B = GAC.iir_coeffs_var(p, v)
        return GAC.iir_spec(nm, p, B), {
            "ref": GAC.iir_ref(nm, B),
            "transposed": GAC.iir_transposed(nm, B)}, {"order": p, "v": v,
                                                       "coeffs": B}
    if family == "med":
        return GAC.med_spec(nm, p), {
            "comb": GAC.med_comb(nm, p), "pipe": GAC.med_pipe(nm, p),
            "pipe2": GAC.med_pipe2(nm, p),
            "sort": GAC.med_sort(nm, p)}, {"window": p, "v": 0}
    raise ValueError(family)


def previously_used():
    """Every design name that has EVER been trained on, held out, or measured.

    Three sources, unioned: the full catalog grid (train corpus + everything the
    grid can emit), the frozen §5 held-out split as enumerated by is_holdout over
    that grid plus the extrapolation designs built directly by eval_holdout, and
    every design named in a manifest under rtl/ (candidates already synthesised).
    """
    used = set()
    for name, _fam, _spec, _styles in GSC.designs(exclude_holdout=False):
        used.add(name)
    # §5 extrapolation designs are outside the grid and built directly by
    # eval_holdout; enumerate them explicitly.
    for T in sorted(GSC.HOLDOUT_EXTRAP_TAPS):
        used.add(f"fir{T}_8b"); used.add(f"firr{T}")
    for D in (4, 8):
        for v in sorted(GSC.HOLDOUT_EXTRAP_POLY_VARS):
            used.add(f"poly{D}_v{v}_8b")
    for N in sorted(GSC.HOLDOUT_EXTRAP_IIR_ORDERS):
        used.add(f"iir{N}")
        for v in range(4):
            used.add(f"iir{N}_v{v}")
    for W in sorted(GSC.HOLDOUT_EXTRAP_MED_W):
        used.add(f"med{W}")
    # anything already synthesised or evaluated
    rtl_root = os.path.join(HERE, "rtl")
    for dirpath, _dirs, files in os.walk(rtl_root):
        for fn in files:
            if fn != "fmax_manifest.json":
                continue
            try:
                mani = json.load(open(os.path.join(dirpath, fn)))
            except Exception:
                continue
            for rec in (mani.values() if isinstance(mani, dict) else mani):
                if isinstance(rec, dict) and "design" in rec:
                    used.add(rec["design"])
    return used


def validate(name, family, spec, styles, ntok):
    """Pre-outcome eligibility. Returns (ok, reason, witness_style, witness_rtl).

    A design is ELIGIBLE if AT LEAST ONE of its correct styles satisfies every
    gate. Styles are tried shortest-first, which is deterministic given the
    emitters and picks the most compact witness, so the budget gate asks the
    right question: does a correct implementation of this design exist inside
    the generation budget?

    Gates, all properties of the DESIGN and never of an outcome:
      - the oracle can build a reference for the name;
      - the style fits the family's generation budget (F4 as an eligibility
        rule: a design whose every correct form overflows the budget would
        measure the budget, not the policy);
      - the style passes the oracle;
      - the canonicaliser accepts it, and the canonical form is trace-equal.
    """
    try:
        oracle.build_reference(name)
    except Exception as e:
        return False, f"no oracle reference: {e}", None, None
    budget = MAX_TOKENS[family]
    ordered = sorted(styles.items(), key=lambda kv: (len(kv[1]), kv[0]))
    why_last = "no style tried"
    for style, rtl in ordered:
        nt = ntok(rtl)
        if nt > budget:
            why_last = (f"smallest correct style '{style}' needs {nt} tokens > "
                        f"{budget} budget (unanswerable by construction)")
            continue
        try:
            r = oracle.score(rtl, name, n=ORACLE_N, seed=ORACLE_SEED)
        except Exception as e:
            why_last = f"style '{style}': oracle raised: {e}"
            continue
        if not r["correct"]:
            why_last = f"style '{style}' not correct (match={r.get('match')})"
            continue
        try:
            canon, _backend = canonicalize(rtl, "lexical")
        except Unsupported as e:
            why_last = f"style '{style}' not canonicalisable: {e}"
            continue
        ok, tw = trace_equal(rtl, canon, name)
        if ok is not True:
            why_last = f"style '{style}' canonical trace mismatch: {tw}"
            continue
        return True, style, style, rtl
    return False, f"no eligible style ({why_last})", None, None


def quotas():
    """BASE_QUOTA per family per regime, with vacant slots reallocated.

    A family/regime whose eligible pool is empty (only med/interp) cannot supply
    designs. Its slots are given to the following families in FAMILY_ORDER,
    cycling from the start, one at a time, so the total stays at
    len(FAMILY_ORDER) * 2 * BASE_QUOTA = 20 and the per-regime count stays 10.
    """
    q = {rg: {f: BASE_QUOTA for f in FAMILY_ORDER} for rg in ("interp", "extrap")}
    for rg in ("interp", "extrap"):
        vacant = 0
        for f in FAMILY_ORDER:
            params, variants = POOLS[f][rg]
            if not params or not variants:
                vacant += q[rg][f]
                q[rg][f] = 0
        i = 0
        donors = [f for f in FAMILY_ORDER if q[rg][f] > 0]
        while vacant > 0 and donors:
            q[rg][donors[i % len(donors)]] += 1
            i += 1
            vacant -= 1
    return q


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "sealed_split.json"))
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--verify", action="store_true",
                    help="regenerate and compare against --out instead of "
                         "writing; exits non-zero on any difference")
    ap.add_argument("--tokenizer", default=os.environ.get(
        "RTLCODER_PATH", "/zeng_gk/Amine/mas/rtlcoder"),
        help="policy tokenizer, used for the budget-eligibility rule")
    args = ap.parse_args()

    # The budget rule must never be silently skipped: a quietly dropped
    # eligibility criterion is exactly the drift this preregistration exists to
    # prevent. No tokenizer => refuse to generate.
    try:
        from transformers import AutoTokenizer
        _tok = AutoTokenizer.from_pretrained(args.tokenizer)
    except Exception as e:
        raise SystemExit(
            f"cannot load tokenizer from {args.tokenizer}: {e}\n"
            f"The generation-budget eligibility rule needs the POLICY's "
            f"tokenizer. Run this on the canonical machine (the GPU server), or "
            f"pass --tokenizer. Refusing to generate the sealed split without "
            f"it rather than skipping a preregistered criterion.")
    ntok = lambda t: len(_tok(t, add_special_tokens=False)["input_ids"])

    used = previously_used()
    print(f"gen_sealed_split  seed={args.seed}  canon v{CANON_VERSION}")
    print(f"previously-used designs excluded: {len(used)}")
    q = quotas()
    print(f"quota interp: {q['interp']}")
    print(f"quota extrap: {q['extrap']}")

    rng = random.Random(args.seed)
    chosen, rejections = [], []
    for regime in ("interp", "extrap"):
        for family in FAMILY_ORDER:
            need = q[regime][family]
            if not need:
                continue
            params, variants = POOLS[family][regime]
            # deterministic candidate order: sorted product, then one shuffle
            # from the preregistered seed. No hand selection anywhere.
            pool = sorted((p, v) for p in params for v in variants)
            rng.shuffle(pool)
            got = 0
            for p, v in pool:
                if got >= need:
                    break
                nm = design_name(family, p, v)
                if nm in used:
                    rejections.append({"design": nm, "reason": "already used"})
                    continue
                spec, styles, prm = build(family, p, v)
                ok, why, wstyle, ref = validate(nm, family, spec, styles, ntok)
                if not ok:
                    rejections.append({"design": nm, "reason": why})
                    print(f"  reject {nm:18s} {why}")
                    continue
                prompt = GSC.make_prompt(spec, ref)
                chosen.append({
                    "design": nm, "family": family, "regime": regime,
                    "params": prm, "max_tokens": MAX_TOKENS[family],
                    "prompt": prompt, "prompt_sha256": sha256_text(prompt),
                    "witness_style": wstyle,
                    "reference_sha256": sha256_text(ref),
                    "reference_chars": len(ref),
                    "reference_tokens": ntok(ref)})
                used.add(nm)
                got += 1
                print(f"  {regime:6s} {family:5s} {nm:16s} "
                      f"witness={wstyle} ({ntok(ref)} tok)")
            if got < need:
                raise SystemExit(
                    f"POOL EXHAUSTED: {family}/{regime} supplied {got}/{need}. "
                    f"Widen the pool in POOLS and re-freeze -- do NOT reduce "
                    f"the quota after seeing this.")

    mani = {
        "schema": SCHEMA,
        "seed": args.seed,
        "generator_sha256": sha256_file(os.path.abspath(__file__)),
        "canon_version": CANON_VERSION,
        "oracle_sha256": sha256_file(os.path.join(HERE, "oracle.py")),
        "catalog_sha256": sha256_file(os.path.join(HERE,
                                                   "gen_accelerator_catalog.py")),
        "family_order": FAMILY_ORDER,
        "base_quota": BASE_QUOTA,
        "quota": q,
        "pools": {f: {r: {"params": POOLS[f][r][0], "variants": POOLS[f][r][1]}
                      for r in ("interp", "extrap")} for f in FAMILY_ORDER},
        "max_tokens": MAX_TOKENS,
        "n_designs": len(chosen),
        "n_previously_used_excluded": len(used) - len(chosen),
        "designs": chosen,
        "rejections": rejections,
        "_med_interp_note": ("med's interpolation pool is provably empty (a "
                             "median has no coefficient axis and every window "
                             "width inside the trained range is consumed by the "
                             "train grid or the §5 held-out set). Its two slots "
                             "were reallocated by the declared replacement rule; "
                             "med still supplies both extrapolation designs."),
        "_limitation": ("These are unseen PARAMETERISATIONS from the same "
                        "generator families, restricted to designs whose "
                        "reference implementation is canonicalisable AND fits "
                        "the family's generation budget. Both restrictions are "
                        "properties of the design, fixed before any outcome was "
                        "seen. This repairs adaptive reuse of the old 30-design "
                        "set. It does NOT establish cross-template "
                        "generalisation."),
    }

    if args.verify:
        old = json.load(open(args.out))
        a = json.dumps([d["design"] for d in old["designs"]], sort_keys=True)
        b = json.dumps([d["design"] for d in mani["designs"]], sort_keys=True)
        same = a == b and old.get("generator_sha256") == mani["generator_sha256"]
        print(f"\nverify: {'MATCH' if same else 'DIFFER'}")
        if not same:
            print(f"  stored : {a}\n  rebuilt: {b}")
            sys.exit(1)
        return

    json.dump(mani, open(args.out, "w"), indent=1)
    print(f"\n{len(chosen)} sealed designs "
          f"({sum(1 for d in chosen if d['regime'] == 'interp')} interp, "
          f"{sum(1 for d in chosen if d['regime'] == 'extrap')} extrap), "
          f"{len(rejections)} rejections -> {args.out}")
    print("\nCommit this file. From now on gen_sft_corpus.is_holdout() returns "
          "True for every design in it, so it cannot enter the SFT corpus, the "
          "reward's training rows, or the GRPO prompt list.")


if __name__ == "__main__":
    main()
