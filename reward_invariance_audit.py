#!/usr/bin/env python3
"""
reward_invariance_audit.py  -  does a candidate reward respond to edits that
cannot change the hardware?

THE GATE. Before a reward is used to optimize a policy, it should be shown not
to move under edits the simulator and the synthesis tool both ignore. A reward
that moves under comment insertion can be raised by writing comments, and no
amount of offline accuracy repairs that.

WHAT THIS MEASURES, AND WHAT IT DOES NOT
----------------------------------------
It measures VULNERABILITY of a reward, not EXPLOITATION by a policy. Those are
different claims and the distinction is load-bearing: of the 116 stored held-out
candidates from the optimized policy, ZERO contain a comment, as do zero of the
159 supervised ones (only the base model writes comments, 19 of 41). So a
comment-channel failure below says the reward COULD be gamed that way, never
that it WAS. Any text derived from this script must preserve that distinction.

TIERS, by what can be proven about them
---------------------------------------
  EXACT     comment insertion, whitespace normalisation. The parsed design is
            unchanged, so the implemented hardware is unchanged and the reward
            must not move at all. Judged against an exact-invariance criterion,
            not a tolerance.

  LEXICAL   scope-limited internal identifier renaming. I/O behaviour is
            unchanged and we verify that by exact trace equality, but internal
            names remain visible to a synthesis tool, which may preserve or
            report them differently. We therefore do NOT claim renaming is
            timing-invariant; we claim it is I/O-equivalent, report it in its
            own tier, and leave the timing question to the canonicalisation
            work.

  SOFT      dead-logic insertion. Synthesis usually strips it but not always
            identically, so real Fmax MAY legitimately move. Never judged
            offline: --emit-soft writes the mutants for run_ppa.py so the
            comparison can be made against re-synthesised numbers.

  Declaration reordering is deliberately absent. Procedural order, declaration
  initialisation and positionally-attached attributes can all make it
  semantics-changing and a tokenizer cannot prove otherwise.

CRITERIA (two, reported separately -- an earlier version conflated them)
-----------------------------------------------------------------------
  exact invariance : max |dPred| <= EPS over candidates the mutation ACTUALLY
                     changed. This is the criterion that matters for EXACT-tier
                     mutations; a tolerance band cannot excuse a deterministic
                     predictor moving at all.
  operational      : does the mutation change anything the optimizer consumes?
                     GRPO z-scores rewards inside a group of samples for one
                     design, so only within-group ORDER and standardized
                     ADVANTAGE drive the gradient. A reward may move by 40 MHz
                     and change no decision, or move by 3 MHz and flip the
                     argmax. Both are reported: pairwise order reversals,
                     top-1 changes, and max |d advantage|.
  severity band    : max(5 MHz, 2%) is retained as a magnitude label only. It
                     was pre-registered but never derived, and pre-registration
                     does not make an arbitrary threshold meaningful.

Denominators are mutation-conditioned: a mutation that leaves a candidate byte
identical cannot be evidence about that candidate, so it is excluded rather than
counted as a pass. Every mutation is drawn with a per-candidate seed, so the
audit does not rest on one mutation pattern.

    python reward_invariance_audit.py --strict-only
    python reward_invariance_audit.py --strict-only --check-oracle --limit 40
    python reward_invariance_audit.py --emit-soft rtl/mutants_soft
"""

import os
import re
import json
import random
import argparse
import collections

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))

EPS = 1e-6           # exact-invariance tolerance: floating point only
ADV_EPS = 1e-3       # advantage shift below this is numerically uninteresting


# ---------------------------------------------------------------- tokenizer
KEYWORDS = set("""
module endmodule input output inout wire reg logic integer parameter localparam
always always_ff always_comb always_latch assign begin end if else for while
case casez casex endcase default posedge negedge or and not xor nand nor xnor
signed unsigned genvar generate endgenerate initial function endfunction task
endtask return automatic static const typedef struct union enum packed void
bit byte shortint int longint real time realtime string chan disable fork join
repeat forever wait specify endspecify defparam
""".split())

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


def header_names(toks):
    """Module name + everything in the port/parameter header. Over-collects on
    purpose: an over-collected name is simply left unrenamed, which is the safe
    direction."""
    names, depth, seen, = set(), 0, False
    for kind, txt in toks:
        if kind in ("ws", "lcomment", "bcomment"):
            continue
        if not seen:
            if kind == "ident" and txt == "module":
                seen = True
            continue
        if kind == "other" and txt in "([":
            depth += 1
        elif kind == "other" and txt in ")]":
            depth -= 1
        elif kind == "other" and txt == ";" and depth <= 0:
            break
        elif kind == "ident" and txt not in KEYWORDS:
            names.add(txt)
    return names


def rename_internals(src, salt):
    """Alpha-rename module-internal identifiers. Tokenizer-based, never regex
    over raw text.

    LIMITATION, stated because the audit is only as good as this: the renamer
    is not declaration-aware. It collects unprotected identifiers appearing
    outside the header rather than proving each one is locally declared. On this
    corpus that is adequate -- the sampled candidates contain no macros,
    functions, tasks, hierarchy, packages, interfaces or multiple modules -- but
    it is NOT a reusable SystemVerilog mutation operator, and every mutant is
    checked for exact I/O-trace equality before its reward movement counts.
    """
    toks = tokenize(src)
    protected = header_names(toks)
    sig = [(k, t) for k, t in toks if k not in ("ws", "lcomment", "bcomment")]
    cand = set()
    for i, (kind, txt) in enumerate(sig):
        if kind != "ident" or txt in KEYWORDS or txt in protected:
            continue
        if i and sig[i - 1][1] == ".":            # .port(sig) connection
            continue
        if i + 1 < len(sig) and sig[i + 1][1] == "(":   # call / instantiation
            continue
        cand.add(txt)
    mapping = {n: f"r{salt}_{i}" for i, n in enumerate(sorted(cand))}
    out = [mapping.get(t, t) if k == "ident" else t for k, t in toks]
    return "".join(out), len(mapping)


# ---------------------------------------------------------------- mutations
FAST_WORDS = ("pipeline stage register transposed unrolled critical path timing "
              "closure fast optimized throughput latency balanced retimed"
              ).split()
NEUTRAL_WORDS = ("note here value signal block section update local copy "
                 "temporary index bound offset element").split()


def mut_comments(src, rng):
    """Insert comments carrying vocabulary associated with FAST designs.

    Adversarial on purpose: if a lexical reward has learned that 'pipeline'
    predicts high frequency, this is the cheapest exploit available to a policy,
    so a neutral-filler test would understate the vulnerability. mut_comments_
    neutral is the control that separates 'reacts to added lines' from 'reacts
    to the words in them'.
    """
    return _insert(src, rng, FAST_WORDS)


def mut_comments_neutral(src, rng):
    return _insert(src, rng, NEUTRAL_WORDS)


def _insert(src, rng, vocab):
    out, n = [], 0
    for ln in src.split("\n"):
        out.append(ln)
        if rng.random() < 0.25:
            out.append("  // " + " ".join(rng.sample(vocab, 4)))
            n += 1
    return "\n".join(out), n


def mut_blanklines(src, rng):
    """Blank lines only: no words at all. Isolates pure line-count sensitivity
    from vocabulary sensitivity."""
    out, n = [], 0
    for ln in src.split("\n"):
        out.append(ln)
        if rng.random() < 0.25:
            out.append("")
            n += 1
    return "\n".join(out), n


def mut_whitespace(src, rng):
    """Re-indent. Never touches string or comment interiors."""
    out = []
    for kind, txt in tokenize(src):
        out.append(("\n" if "\n" in txt else "  ") if kind == "ws" else txt)
    return "".join(out), 1


def mut_rename(src, rng):
    return rename_internals(src, rng.randint(1000, 9999))


def mut_deadcode(src, rng):
    m = re.search(r"\bendmodule\b", src)
    if not m:
        return src, 0
    dead = "\n".join(f"  wire [{rng.randint(1, 31)}:0] dead_{i}_unused;"
                     for i in range(4))
    return src[:m.start()] + dead + "\n" + src[m.start():], 4


EXACT = [("comments_fast", mut_comments), ("comments_neutral", mut_comments_neutral),
         ("blanklines", mut_blanklines), ("whitespace", mut_whitespace)]
LEXICAL = [("rename", mut_rename)]
SOFT = [("deadcode", mut_deadcode)]
TIER = ({n: "EXACT" for n, _ in EXACT} | {n: "LEXICAL" for n, _ in LEXICAL}
        | {n: "SOFT" for n, _ in SOFT})


# ---------------------------------------------------------------- metrics
def group_metrics(test, base, mut, changed):
    """Everything the optimizer would actually notice.

    GRPO standardizes rewards inside a (policy, design) group, so scale is
    irrelevant and only order and standardized advantage matter. A 40 MHz shift
    that preserves the ordering changes no gradient; a 3 MHz shift that flips
    the argmax does.
    """
    by = collections.defaultdict(list)
    for i, t in enumerate(test):
        by[(t["policy"], t["design"])].append(i)
    rev = top1 = groups = 0
    dadv = 0.0
    for _, idx in by.items():
        if len(idx) < 2 or not any(changed[i] for i in idx):
            continue
        groups += 1
        b = np.array([base[i] for i in idx])
        m = np.array([mut[i] for i in idx])
        for a in range(len(idx)):
            for c in range(a + 1, len(idx)):
                if np.sign(b[a] - b[c]) != np.sign(m[a] - m[c]):
                    rev += 1
        if int(np.argmax(b)) != int(np.argmax(m)):
            top1 += 1
        ab = (b - b.mean()) / (b.std() + 1e-8)
        am = (m - m.mean()) / (m.std() + 1e-8)
        dadv = max(dadv, float(np.abs(ab - am).max()))
    return {"groups_touched": groups, "pair_reversals": rev,
            "top1_changes": top1, "max_abs_dadvantage": dadv}


def stratify(test, base, mut, changed):
    out = {}
    by = collections.defaultdict(list)
    for i, t in enumerate(test):
        if changed[i]:
            by[t["policy"]].append(i)
    for pol, idx in by.items():
        d = np.array([mut[i] - base[i] for i in idx])
        out[pol] = {"n_changed": len(idx), "mean_signed": float(d.mean()),
                    "max_abs": float(np.abs(d).max()),
                    "n_increases": int((d > 0).sum()),
                    "n_decreases": int((d < 0).sum())}
    return out


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dirs", nargs="*", default=[
        "rtl/holdout_eval_v8_firfirr", "rtl/holdout_eval_v8_poly",
        "rtl/holdout_eval_v8_iirmed"])
    ap.add_argument("--train-dirs", nargs="*", default=[
        "rtl/fmax_probe_v4", "rtl/fmax_data", "rtl/policy_cmp", "rtl/fmax_d2"])
    ap.add_argument("--ckpt", default=os.path.join(HERE, "surrogate_v3.pt"))
    ap.add_argument("--limit", type=int, default=0,
                    help="0 = every candidate (default). Sampling is only for "
                         "the slow --check-oracle pass.")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--strict-only", action="store_true")
    ap.add_argument("--emit-soft", default="")
    ap.add_argument("--check-oracle", action="store_true",
                    help="prove each mutant is I/O-identical to its original by "
                         "comparing FULL TRACES on identical stimuli, not merely "
                         "by both scoring correct")
    ap.add_argument("--oracle-seeds", type=int, nargs="*", default=[1, 2])
    ap.add_argument("--out", default=os.path.join(HERE, "reward_invariance.json"))
    args = ap.parse_args()

    import surrogate_arch_ablation as A

    train = A.read_train(args.train_dirs)
    test = A.read_test(args.dirs)
    if args.limit:
        random.Random(args.seed).shuffle(test)
        test = test[:args.limit]
    print(f"train rows: {len(train)}   candidates: {len(test)}")
    pols = collections.Counter(t["policy"] for t in test)
    print(f"by policy: {dict(pols)}")
    ncom = sum(1 for t in test if "//" in t["txt"])
    print(f"candidates that ALREADY contain a comment: {ncom}/{len(test)}  "
          f"({dict(collections.Counter(t['policy'] for t in test if '//' in t['txt']))})")
    print("  -> a comment-channel failure is a VULNERABILITY of the reward, not\n"
          "     evidence the policy used it.\n")

    muts = EXACT + LEXICAL + ([] if args.strict_only else SOFT)
    variants, changed_mask, stats = {}, {}, {}
    for name, fn in muts:
        outs, ch = [], []
        for i, t in enumerate(test):
            r = random.Random(args.seed * 100003 + i)   # per-candidate pattern
            s, _ = fn(t["txt"], r)
            outs.append(s)
            ch.append(s != t["txt"])
        variants[name] = outs
        changed_mask[name] = ch
        stats[name] = {"tier": TIER[name], "n_changed": int(sum(ch)),
                       "n": len(test)}
        print(f"  {name:17s} [{TIER[name]:7s}] changed {sum(ch):4d}/{len(test)}")

    # ---- prove the mutants are I/O-identical ------------------------------
    if args.check_oracle:
        import oracle
        print("\nproving mutants are I/O-identical (full trace equality, "
              f"seeds {args.oracle_seeds}) ...")
        fails = collections.Counter()
        checked = collections.Counter()
        for name in [n for n, _ in EXACT + LEXICAL]:
            for t, s in zip(test, variants[name]):
                if s == t["txt"]:
                    continue
                d = t["design"]
                o = re.sub(r"\bmodule\s+\w+", f"module {d}", t["txt"], 1)
                m = re.sub(r"\bmodule\s+\w+", f"module {d}", s, 1)
                try:
                    _, in_w = oracle.build_reference(d)
                    same = True
                    for sd in args.oracle_seeds:
                        stim = oracle.gen_stimulus(256, in_w, sd)
                        a = oracle.run_dut(o, d, stim, in_w)
                        b = oracle.run_dut(m, d, stim, in_w)
                        if a is None or b is None or len(a) != len(b) \
                                or not bool((a == b).all()):
                            same = False
                            break
                except Exception:
                    same = False
                checked[name] += 1
                if not same:
                    fails[name] += 1
            print(f"  {name:17s}: {fails[name]:3d} of {checked[name]:3d} mutants "
                  f"are NOT trace-identical"
                  + ("   <-- MUTATION UNSAFE, its reward numbers are void"
                     if fails[name] else ""))
        stats["oracle_trace_failures"] = dict(fails)
        stats["oracle_trace_checked"] = dict(checked)

    if args.emit_soft and not args.strict_only:
        os.makedirs(args.emit_soft, exist_ok=True)
        mani = {}
        for i, (t, s) in enumerate(zip(test, variants["deadcode"])):
            mod = f"soft{i:04d}"
            open(os.path.join(args.emit_soft, mod + ".sv"), "w").write(
                re.sub(r"\bmodule\s+\w+", f"module {mod}", s, 1))
            mani[mod] = {"policy": t["policy"], "design": t["design"],
                         "count": 1, "n": 1, "orig_fmax": t["fmax"]}
        json.dump(mani, open(os.path.join(args.emit_soft, "fmax_manifest.json"),
                             "w"), indent=1)
        print(f"\nwrote {len(mani)} SOFT mutants to {args.emit_soft}/")

    # ---- score ------------------------------------------------------------
    Xtr = np.array([r["feats"] for r in train], float)
    ytr = np.log(np.array([r["fmax"] for r in train], float))
    Ttr = [r["txt"] for r in train]

    results = {}
    print(f"\n{'reward':16s} {'mutation':17s} {'chg':>5s} {'max|d|':>8s} "
          f"{'mean d':>8s} {'revrs':>6s} {'top1':>5s} {'dAdv':>7s} "
          f"{'exact':>6s} {'operational':>12s}")
    print("-" * 104)
    for name, space, mk in A.architectures(1):
        def score(texts):
            if space == "ckpt":
                if not os.path.exists(args.ckpt):
                    return None
                return np.exp(np.clip(A.predict_deployed(args.ckpt, texts),
                                      np.log(A.CLAMP_LO), np.log(A.CLAMP_HI)))
            f = np.array([A.extract_features(x) for x in texts], float)
            if space == "feats" and mk is None:
                pl = A.fit_mlp(Xtr, ytr, f, seed=0)
            elif space == "feats":
                pl = A.fit_sklearn(mk(), Xtr, ytr, f)
            else:
                pl = A.fit_sklearn(mk(), Ttr, ytr, texts)
            return np.exp(np.clip(pl, np.log(A.CLAMP_LO), np.log(A.CLAMP_HI)))

        base = score([t["txt"] for t in test])
        if base is None:
            print(f"{name:16s} [skipped: {args.ckpt} absent]")
            continue
        rows = {}
        for mname, _ in muts:
            mp = score(variants[mname])
            ch = changed_mask[mname]
            sel = [i for i, c in enumerate(ch) if c]
            if not sel:
                continue
            d = np.array([mp[i] - base[i] for i in sel])
            tol = np.array([max(5.0, 0.02 * base[i]) for i in sel])
            g = group_metrics(test, base, mp, ch)
            exact_ok = float(np.abs(d).max()) <= EPS
            oper_bad = (g["pair_reversals"] > 0 or g["top1_changes"] > 0
                        or g["max_abs_dadvantage"] > ADV_EPS)
            rows[mname] = {
                "tier": TIER[mname], "n_changed": len(sel),
                "max_abs": float(np.abs(d).max()),
                "mean_signed": float(d.mean()),
                "n_over_severity_band": int((np.abs(d) > tol).sum()),
                "exact_invariant": bool(exact_ok),
                "operationally_clean": bool(not oper_bad),
                **g, "by_policy": stratify(test, base, mp, ch)}
            print(f"{name:16s} {mname:17s} {len(sel):5d} "
                  f"{np.abs(d).max():8.1f} {d.mean():+8.2f} "
                  f"{g['pair_reversals']:6d} {g['top1_changes']:5d} "
                  f"{g['max_abs_dadvantage']:7.3f} "
                  f"{'ok' if exact_ok else 'FAIL':>6s} "
                  f"{'ok' if not oper_bad else 'FAIL':>12s}")
        results[name] = rows
        print()

    json.dump({"stats": stats, "results": results}, open(args.out, "w"), indent=1)
    print(f"wrote {args.out}\n")
    print("Read the two verdict columns separately.")
    print("  exact       : did a deterministic predictor move at all under an")
    print("                edit that cannot change the parsed design?")
    print("  operational : did anything the optimizer consumes change --")
    print("                within-group ORDER, the argmax, or the standardized")
    print("                advantage? A reward can fail 'exact' and still be")
    print("                operationally inert, and that distinction decides")
    print("                whether a failure is cosmetic or load-bearing.")
    print("\nNeither column licenses a claim that the POLICY used a channel.")
    print("Check the per-policy stratification and the already-contains-comment")
    print("count above before writing anything about observed behaviour.")


if __name__ == "__main__":
    main()
