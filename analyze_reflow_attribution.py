#!/usr/bin/env python3
"""
analyze_reflow_attribution.py  -  how much of the late reward jump is layout?

THE CLOSING ARGUMENT of the v8 diagnosis. Between checkpoints s300 and s400 the
deployed reward rises by roughly 281 MHz while real post-implementation Fmax
moves by about -1. Over the same interval the generated RTL gains ~20 lines and
~20 line-initial nonblocking assignments while its TOKEN COUNT FALLS. The code
got smaller and more spread out.

That is consistent with the policy having found a layout channel:
`nb_assign` is `^\\s*\\w+(\\[..\\])?\\s*<=` with MULTILINE, so it counts
assignments that BEGIN A LINE. Packed as `a0 <= 0; a1 <= 0; a2 <= 0;` it scores
1; split one per line it scores 3. Identical hardware.

This script decides how much of the jump that explains, by re-scoring every
stored trajectory candidate under a LAYOUT-CANONICAL form and comparing:

    raw       the text as generated, which is what the reward saw in training
    canonical comments stripped, statements re-emitted one per line, internal
              whitespace collapsed -- a deterministic layout that does not
              depend on how the model chose to format

If the s300->s400 jump largely disappears under canonicalisation, the late gain
was layout rather than hardware, and canonicalisation is the targeted repair.
If it survives, the policy changed something real and the layout story is wrong.
Both answers are reported; the script does not choose.

It also finds trajectory candidates from DIFFERENT checkpoints that are
token-identical (same tokens, different layout) and prints their raw rewards
side by side. Those pairs are the cleanest possible evidence: identical token
stream, identical hardware, different reward.

Run on the server, where surrogate_v3.pt lives:
    python -u analyze_reflow_attribution.py --ckpt surrogate_v3.pt \\
        --out reflow_attribution.json
"""

import os
import re
import json
import argparse
import collections

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
UPDATES = {"step0": 0, "s100": 77, "s200": 138, "s300": 205, "s400": 276}

# token stream used for the "same hardware, different layout" test. Deliberately
# layout-blind and comment-blind: if two candidates agree here they differ only
# in trivia the simulator and the synthesis tool both ignore.
TOKEN = re.compile(r"[A-Za-z_][A-Za-z0-9_$]*|[0-9]+'[sSbBoOdDhH]*[0-9a-fA-FxXzZ_]+"
                   r"|[0-9]+|\S")
LINE_COMMENT = re.compile(r"//[^\n]*")
BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)


def strip_comments(txt):
    return LINE_COMMENT.sub("", BLOCK_COMMENT.sub("", txt))


def tokens(txt):
    return TOKEN.findall(strip_comments(txt))


def canonical_layout(txt):
    """Deterministic layout: one statement per line, single-spaced.

    Chosen because it is INDEPENDENT of the generator's formatting decisions.
    Any layout convention would do -- what matters is that every candidate gets
    the same one, so `n_lines` and `nb_assign` become functions of the design
    rather than of how the model chose to press Enter. Statement boundaries are
    ';', 'begin' and 'end', which is adequate for this corpus and is checked by
    the token-identity assertion below.
    """
    t = strip_comments(txt)
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"\s*;\s*", ";\n", t)
    t = re.sub(r"\bbegin\b", "begin\n", t)
    t = re.sub(r"\bend\b", "\nend\n", t)
    out = [ln.strip() for ln in t.split("\n")]
    return "\n".join(ln for ln in out if ln)


def load_traj(d):
    mani = json.load(open(os.path.join(d, "fmax_manifest.json")))
    real = {}
    p = os.path.join(d, "ppa.jsonl")
    if os.path.exists(p):
        for line in open(p):
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r.get("compiled"):
                real[r["module"]] = float(r["fmax_mhz"])
    out = []
    for mod, i in mani.items():
        f = os.path.join(d, mod + ".sv")
        if not os.path.exists(f):
            continue
        txt = open(f, errors="replace").read()
        out.append({"mod": mod, "ckpt": i["policy"], "design": i["design"],
                    "count": i["count"], "txt": txt,
                    "canon": canonical_layout(txt),
                    "tok": tuple(tokens(txt)),
                    "real": real.get(mod)})
    return out


def wmean(rows, key, weight="count"):
    w = sum(r[weight] for r in rows)
    return sum(r[key] * r[weight] for r in rows) / w if w else float("nan")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dirs", nargs="*",
                    default=[os.path.join(HERE, "rtl", "traj_v8")])
    ap.add_argument("--ckpt", default=os.path.join(HERE, "surrogate_v3.pt"))
    ap.add_argument("--out", default=os.path.join(HERE, "reflow_attribution.json"))
    args = ap.parse_args()

    from rescore_surrogate import load_surrogate
    from surrogate_train import feature_dict
    predict, _ = load_surrogate(args.ckpt)

    rows = []
    for d in args.dirs:
        rows += load_traj(d)
    print(f"{len(rows)} trajectory candidates from {len(args.dirs)} dir(s)")

    # sanity: canonicalisation must not change the token stream
    bad = sum(1 for r in rows if tuple(tokens(r["canon"])) != r["tok"])
    print(f"canonicalisation changed the token stream on {bad}/{len(rows)} "
          f"candidates" + ("   <-- CANONICALISER IS LOSSY, results void"
                           if bad else "   (lossless)"))

    for r in rows:
        r["raw_pred"] = predict(r["txt"])
        r["canon_pred"] = predict(r["canon"])
        fr, fc = feature_dict(r["txt"]), feature_dict(r["canon"])
        r["lines_raw"], r["lines_canon"] = fr["n_lines"], fc["n_lines"]
        r["nb_raw"], r["nb_canon"] = fr["nb_assign"], fc["nb_assign"]
        r["ntok"] = len(r["tok"])

    by = collections.defaultdict(list)
    for r in rows:
        by[r["ckpt"]].append(r)

    print(f"\n{'ckpt':7s} {'upd':>4s} {'raw pred':>9s} {'canon pred':>11s} "
          f"{'real':>8s} {'lines':>7s} {'nb_raw':>7s} {'nb_can':>7s} {'tokens':>7s}")
    print("-" * 78)
    summary = {}
    for ck in sorted(by, key=lambda k: UPDATES.get(k, 0)):
        rs = by[ck]
        got = [r for r in rs if r["real"] is not None]
        s = {"updates": UPDATES.get(ck, 0),
             "raw_pred": wmean(rs, "raw_pred"),
             "canon_pred": wmean(rs, "canon_pred"),
             "real": wmean(got, "real") if got else float("nan"),
             "lines": wmean(rs, "lines_raw"),
             "nb_raw": wmean(rs, "nb_raw"),
             "nb_canon": wmean(rs, "nb_canon"),
             "tokens": wmean(rs, "ntok"), "n": len(rs)}
        summary[ck] = s
        print(f"{ck:7s} {s['updates']:4d} {s['raw_pred']:9.1f} "
              f"{s['canon_pred']:11.1f} {s['real']:8.1f} {s['lines']:7.1f} "
              f"{s['nb_raw']:7.1f} {s['nb_canon']:7.1f} {s['tokens']:7.1f}")

    # ---- the attribution number -------------------------------------------
    if "s300" in summary and "s400" in summary:
        a, b = summary["s300"], summary["s400"]
        d_raw = b["raw_pred"] - a["raw_pred"]
        d_can = b["canon_pred"] - a["canon_pred"]
        d_real = b["real"] - a["real"]
        expl = (1.0 - d_can / d_raw) * 100.0 if abs(d_raw) > 1e-9 else float("nan")
        print(f"\ns300 -> s400")
        print(f"  reward jump, raw layout        {d_raw:+8.1f} MHz")
        print(f"  reward jump, canonical layout  {d_can:+8.1f} MHz")
        print(f"  real Vivado change             {d_real:+8.1f} MHz")
        print(f"  share of the jump removed by canonicalisation: {expl:.1f}%")
        summary["_attribution"] = {"d_raw": d_raw, "d_canon": d_can,
                                   "d_real": d_real, "pct_removed": expl}

    # ---- token-identical pairs across checkpoints -------------------------
    groups = collections.defaultdict(list)
    for r in rows:
        groups[(r["design"], r["tok"])].append(r)
    pairs = []
    for (des, _), rs in groups.items():
        cks = {r["ckpt"] for r in rs}
        if len(cks) < 2:
            continue
        lo = min(rs, key=lambda r: r["raw_pred"])
        hi = max(rs, key=lambda r: r["raw_pred"])
        if hi["raw_pred"] - lo["raw_pred"] < 1.0:
            continue
        pairs.append({"design": des, "lo_ckpt": lo["ckpt"], "hi_ckpt": hi["ckpt"],
                      "lo_pred": lo["raw_pred"], "hi_pred": hi["raw_pred"],
                      "lo_lines": lo["lines_raw"], "hi_lines": hi["lines_raw"],
                      "lo_nb": lo["nb_raw"], "hi_nb": hi["nb_raw"],
                      "lo_real": lo["real"], "hi_real": hi["real"],
                      "lo_mod": lo["mod"], "hi_mod": hi["mod"]})
    pairs.sort(key=lambda p: p["lo_pred"] - p["hi_pred"])
    print(f"\nTOKEN-IDENTICAL candidates whose reward differs: {len(pairs)}")
    if pairs:
        print("identical token stream => identical hardware. Any reward gap is\n"
              "layout alone.\n")
        print(f"{'design':12s} {'from':6s} {'to':6s} {'pred':>15s} "
              f"{'lines':>11s} {'nb_assign':>11s} {'real MHz':>15s}")
        for p in pairs[:12]:
            lr = "n/a" if p["lo_real"] is None else f"{p['lo_real']:.0f}"
            hr = "n/a" if p["hi_real"] is None else f"{p['hi_real']:.0f}"
            print(f"{p['design']:12s} {p['lo_ckpt']:6s} {p['hi_ckpt']:6s} "
                  f"{p['lo_pred']:6.1f}->{p['hi_pred']:7.1f} "
                  f"{p['lo_lines']:4.0f}->{p['hi_lines']:4.0f} "
                  f"{p['lo_nb']:5.0f}->{p['hi_nb']:4.0f} "
                  f"{lr:>7s}->{hr:>7s}")

    json.dump({"summary": summary, "token_identical_pairs": pairs},
              open(args.out, "w"), indent=1)
    print(f"\nwrote {args.out}")
    print("\nReading: 'share removed by canonicalisation' is the attribution.")
    print("High => the late reward gain was layout, and canonicalisation is the")
    print("targeted repair. Low => the policy changed something real and the")
    print("layout account is wrong. The token-identical pairs are the same claim")
    print("without any modelling at all: same tokens, same hardware, different")
    print("reward.")


if __name__ == "__main__":
    main()
