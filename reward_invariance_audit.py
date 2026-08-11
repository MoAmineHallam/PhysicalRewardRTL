#!/usr/bin/env python3
"""
reward_invariance_audit.py  -  does a candidate reward respond to changes that
cannot alter the hardware?

THE GATE. Before any reward is used to optimize a policy, it must be shown not
to move under edits the oracle and the synthesis tool both ignore. A reward that
moves under comment insertion is a reward a policy can raise by writing
comments, and no amount of offline accuracy repairs that.

Two tiers, because they are not the same kind of evidence.

  STRICT  comment insertion, whitespace normalisation, scope-limited internal
          identifier renaming. These provably cannot change the implemented
          hardware, so real Fmax is unchanged by construction and ANY reward
          movement is a defect. No synthesis is needed to judge them.

  SOFT    dead-logic insertion. Synthesis usually removes it but not always
          identically, so real Fmax MAY legitimately move. These cannot be
          judged without re-synthesising, and this script only PREPARES them:
          it writes the mutants to a directory for run_ppa.py and records the
          predictions, so the comparison can be made once real numbers exist.
          Declaration reordering is deliberately NOT implemented -- procedural
          order, declaration initialisation and positional attributes can all
          make it semantics-changing, and a lexer alone cannot prove otherwise.

Identifier renaming is tokenizer-based, never regex over raw text. It renames
only identifiers that are declared inside the module body and are not: the
module name, any port, a Verilog keyword, a system task, a macro, an escaped
identifier, or anything appearing inside a string or comment. Anything it cannot
prove safe, it leaves alone -- the audit is worthless if the mutation itself
changes behaviour, so it errs toward mutating less.

    python reward_invariance_audit.py --strict-only
    python reward_invariance_audit.py --emit-soft rtl/mutants_soft

Predeclared rejection rule for the STRICT tier, fixed before running:
    a reward FAILS if any strict mutation moves its prediction by more than
    max(5 MHz, 2% of the original prediction), or changes the ordering of any
    two candidates of the same design.
Predictors here are deterministic, so there is no sampling noise to excuse a
movement.
"""

import os
import re
import json
import random
import argparse
import collections

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- tokenizer
KEYWORDS = set("""
module endmodule input output inout wire reg logic integer parameter localparam
always always_ff always_comb always_latch assign begin end if else for while
case casez casex endcase default posedge negedge or and not xor nand nor xnor
signed unsigned genvar generate endgenerate initial function endfunction task
endtask return automatic static const typedef struct union enum packed void
bit byte shortint int longint real time realtime string chan disable fork join
repeat forever wait sepcify endspecify defparam
""".split())

# strings, comments, escaped identifiers, sized/based numbers, identifiers,
# whitespace, everything else. Order matters: longest / most specific first.
TOK = re.compile(r"""
    (?P<ws>\s+)
  | (?P<lcomment>//[^\n]*)
  | (?P<bcomment>/\*.*?\*/)
  | (?P<string>"(?:\\.|[^"\\])*")
  | (?P<escid>\\[^\s]+\s)
  | (?P<macro>`[A-Za-z_][A-Za-z0-9_$]*)
  | (?P<number>[0-9]*'[sS]?[bBoOdDhH][0-9a-fA-FxXzZ_?]+|[0-9][0-9_]*(?:\.[0-9_]+)?)
  | (?P<ident>[A-Za-z_][A-Za-z0-9_$]*)
  | (?P<other>.)
""", re.VERBOSE | re.DOTALL)


def tokenize(src):
    return [(m.lastgroup, m.group()) for m in TOK.finditer(src)]


def module_header_names(toks, design):
    """Module name + every port identifier, which must never be renamed.

    Conservative: takes every identifier between 'module' and the ';' that ends
    the header. That over-collects (it includes type keywords' neighbours and
    parameter names), which is the safe direction -- an over-collected name is
    simply left unrenamed.
    """
    names, depth, seen_module, i = set(), 0, False, 0
    for kind, txt in toks:
        if kind in ("ws", "lcomment", "bcomment"):
            continue
        if not seen_module:
            if kind == "ident" and txt == "module":
                seen_module = True
            continue
        if kind == "other" and txt in "([":
            depth += 1
        elif kind == "other" and txt in ")]":
            depth -= 1
        elif kind == "other" and txt == ";" and depth <= 0:
            break
        elif kind == "ident" and txt not in KEYWORDS:
            names.add(txt)
    names.add(design)
    return names


def rename_internals(src, design, salt):
    """Alpha-rename module-internal identifiers only. Returns (text, n_renamed)."""
    toks = tokenize(src)
    protected = module_header_names(toks, design)
    # candidates: identifiers that appear outside the header, are not keywords,
    # not protected, not immediately preceded by '.' (port connection / member),
    # and not immediately followed by '(' (task / function / instance call).
    counts = collections.Counter()
    prev_sig, nxt = None, None
    sig = [(k, t) for k, t in toks if k not in ("ws", "lcomment", "bcomment")]
    for idx, (kind, txt) in enumerate(sig):
        if kind != "ident" or txt in KEYWORDS or txt in protected:
            continue
        if idx and sig[idx - 1][1] == ".":
            continue
        if idx + 1 < len(sig) and sig[idx + 1][1] == "(":
            continue
        if txt.startswith("$"):
            continue
        counts[txt] += 1
    mapping = {n: f"r{salt}_{i}" for i, n in enumerate(sorted(counts))}
    out = []
    for kind, txt in toks:
        if kind == "ident" and txt in mapping:
            out.append(mapping[txt])
        else:
            out.append(txt)
    return "".join(out), len(mapping)


# ---------------------------------------------------------------- mutations
WORDS = ("pipeline stage register transposed unrolled critical path timing "
         "closure fast optimized throughput latency balanced retimed").split()


def mut_comments(src, rng):
    """Insert comments containing vocabulary associated with FAST designs.

    Deliberately adversarial: if a lexical reward has learned that the word
    'pipeline' predicts high frequency, this is the cheapest way for a policy to
    exploit it, and the mutation must therefore be exactly that attack rather
    than neutral filler.
    """
    lines = src.split("\n")
    out, n = [], 0
    for ln in lines:
        out.append(ln)
        if rng.random() < 0.25:
            out.append("  // " + " ".join(rng.sample(WORDS, 4)))
            n += 1
    return "\n".join(out), n


def mut_whitespace(src, rng):
    """Reindent and pad. Never touches string or comment interiors."""
    out = []
    for kind, txt in tokenize(src):
        if kind == "ws":
            out.append("\n" if "\n" in txt else "  ")
        else:
            out.append(txt)
    return "".join(out), 1


def mut_rename(src, rng, design=""):
    return rename_internals(src, design, rng.randint(1000, 9999))


def mut_deadcode(src, rng):
    """SOFT tier: unused declarations synthesis is expected to strip.

    Not judged offline. Written out for re-synthesis, because 'expected to
    strip' is not 'provably stripped', and a real frequency change here would
    make reward movement legitimate rather than a defect.
    """
    m = re.search(r"\bendmodule\b", src)
    if not m:
        return src, 0
    dead = "\n".join(
        f"  wire [{rng.randint(1, 31)}:0] dead_{i}_unused;" for i in range(4))
    return src[:m.start()] + dead + "\n" + src[m.start():], 4


STRICT = [("comments", mut_comments), ("whitespace", mut_whitespace),
          ("rename", mut_rename)]
SOFT = [("deadcode", mut_deadcode)]


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dirs", nargs="*", default=[
        "rtl/holdout_eval_v8_firfirr", "rtl/holdout_eval_v8_poly",
        "rtl/holdout_eval_v8_iirmed"])
    ap.add_argument("--train-dirs", nargs="*", default=[
        "rtl/fmax_probe_v4", "rtl/fmax_data", "rtl/policy_cmp", "rtl/fmax_d2"])
    ap.add_argument("--ckpt", default=os.path.join(HERE, "surrogate_v3.pt"))
    ap.add_argument("--limit", type=int, default=120,
                    help="candidates to mutate (sampled with a fixed seed)")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--strict-only", action="store_true")
    ap.add_argument("--emit-soft", default="",
                    help="directory to write SOFT-tier mutants for run_ppa.py")
    ap.add_argument("--check-oracle", action="store_true",
                    help="verify each strict mutant is still oracle-correct "
                         "(needs iverilog; slow but this is the whole premise)")
    ap.add_argument("--out", default=os.path.join(HERE, "reward_invariance.json"))
    args = ap.parse_args()

    import surrogate_arch_ablation as A
    rng = random.Random(args.seed)

    train = A.read_train(args.train_dirs)
    test = A.read_test([d for d in args.dirs])
    rng.shuffle(test)
    test = test[:args.limit]
    print(f"train rows: {len(train)}   candidates to mutate: {len(test)}")

    # ---- build the mutant set --------------------------------------------
    variants = {"original": [t["txt"] for t in test]}
    stats = {}
    for name, fn in (STRICT if args.strict_only else STRICT + SOFT):
        muts, touched = [], 0
        for t in test:
            r = random.Random(args.seed)
            if name == "rename":
                s, n = mut_rename(t["txt"], r, t["design"])
            else:
                s, n = fn(t["txt"], r)
            muts.append(s)
            touched += (1 if n else 0)
        variants[name] = muts
        stats[name] = {"candidates_changed": touched, "n": len(test)}
        print(f"  mutation {name:11s}: changed {touched}/{len(test)} candidates")

    if args.check_oracle:
        import oracle
        print("\nverifying strict mutants preserve oracle behaviour ...")
        bad = collections.Counter()
        for name in [n for n, _ in STRICT]:
            for t, s in zip(test, variants[name]):
                stem = re.sub(r"\bmodule\s+\w+", f"module {t['design']}", s, 1)
                try:
                    ok = oracle.score(stem, t["design"], n=256, seed=1)["correct"]
                except Exception:
                    ok = False
                if not ok:
                    bad[name] += 1
            print(f"  {name:11s}: {bad[name]} of {len(test)} mutants no longer "
                  f"score correct" + ("   <-- MUTATION IS UNSAFE" if bad[name]
                                      else ""))
        stats["oracle_failures"] = dict(bad)

    if args.emit_soft and not args.strict_only:
        os.makedirs(args.emit_soft, exist_ok=True)
        mani = {}
        for i, (t, s) in enumerate(zip(test, variants["deadcode"])):
            mod = f"soft{i:04d}"
            open(os.path.join(args.emit_soft, mod + ".sv"), "w").write(
                re.sub(r"\bmodule\s+\w+", f"module {mod}", s, 1))
            mani[mod] = {"policy": t["policy"], "design": t["design"],
                         "count": 1, "n": 1, "orig_fmax": t["fmax"]}
        json.dump(mani, open(os.path.join(args.emit_soft,
                                          "fmax_manifest.json"), "w"), indent=1)
        print(f"\nwrote {len(mani)} SOFT mutants to {args.emit_soft}/ "
              f"-- run run_ppa.py there, then compare against orig_fmax")

    # ---- score every variant with every reward ---------------------------
    Xtr = np.array([r["feats"] for r in train], float)
    ytr = np.log(np.array([r["fmax"] for r in train], float))
    Ttr = [r["txt"] for r in train]

    results = {}
    print(f"\n{'reward':16s} {'mutation':11s} {'max |dPred|':>12s} "
          f"{'mean |dPred|':>13s} {'> tol':>8s} {'verdict':>9s}")
    print("-" * 76)
    for name, space, mk in A.architectures(1):
        def score(texts):
            if space == "ckpt":
                if not os.path.exists(args.ckpt):
                    return None
                return np.exp(np.clip(A.predict_deployed(args.ckpt, texts),
                                      np.log(A.CLAMP_LO), np.log(A.CLAMP_HI)))
            feats = np.array([A.extract_features(x) for x in texts], float)
            if space == "feats" and mk is None:
                pl = A.fit_mlp(Xtr, ytr, feats, seed=0)
            elif space == "feats":
                pl = A.fit_sklearn(mk(), Xtr, ytr, feats)
            else:
                pl = A.fit_sklearn(mk(), Ttr, ytr, texts)
            return np.exp(np.clip(pl, np.log(A.CLAMP_LO), np.log(A.CLAMP_HI)))

        base = score(variants["original"])
        if base is None:
            print(f"{name:16s} [skipped: {args.ckpt} absent]")
            continue
        rows, failed = {}, False
        for mname in [k for k in variants if k != "original"]:
            mp = score(variants[mname])
            d = np.abs(mp - base)
            tol = np.maximum(5.0, 0.02 * base)
            n_over = int((d > tol).sum())
            tier = "STRICT" if mname in [n for n, _ in STRICT] else "soft"
            bad = tier == "STRICT" and n_over > 0
            failed |= bad
            rows[mname] = {"max_abs": float(d.max()), "mean_abs": float(d.mean()),
                           "n_over_tol": n_over, "n": len(d), "tier": tier}
            print(f"{name:16s} {mname:11s} {d.max():12.1f} {d.mean():13.1f} "
                  f"{n_over:5d}/{len(d):<4d} "
                  f"{'FAIL' if bad else ('ok' if tier == 'STRICT' else 'defer'):>9s}")
        results[name] = {"rows": rows, "strict_pass": not failed}
        print()

    json.dump({"stats": stats, "results": results}, open(args.out, "w"), indent=1)
    print(f"wrote {args.out}\n")
    print("STRICT verdict: a reward that moves at all under comment insertion,")
    print("whitespace, or internal renaming is exploitable by a policy that")
    print("edits any of them, and must not be used as a training signal.")
    print("SOFT rows say 'defer': dead code may legitimately change real Fmax,")
    print("so judge them only against re-synthesised numbers (--emit-soft).")


if __name__ == "__main__":
    main()
