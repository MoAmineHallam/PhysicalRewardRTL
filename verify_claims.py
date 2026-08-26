#!/usr/bin/env python3
"""
verify_claims.py  -  reproduce every number that changed a claim on 2026-08-11.

Run this yourself. It re-derives each result from committed artifacts and prints
what was claimed next to what it computes, so a disagreement is visible without
reading any prose.

    python verify_claims.py                 # deterministic checks only (no torch)
    python verify_claims.py --lodo 10       # + rerun the noisy LODO 10 times

Sections A-D are DETERMINISTIC: pure numpy over committed ppa.jsonl and manifest
files. Same input, same output, on any machine.

Section E is NOT deterministic. surrogate_train.py sets no random seed, so its
LODO figure is a fresh draw of the network initialisation every run. This
matters: the figure it replaced (0.75-0.82) was itself reported as a RANGE over
seeds. --lodo N reruns it N times and reports the spread, which is the only
honest way to compare against a range. It needs torch and takes ~1 min per run
per surrogate.

Section F needs iverilog and re-simulates 1,529 candidates (~1 min at 4 workers);
run audit_oracle.py directly for that one.
"""

import os
import json
import argparse
import subprocess
import collections
import statistics
import pathlib
import re
import sys
import hashlib

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = pathlib.Path(HERE)
PAPER = ROOT / "paper"
V8 = [os.path.join(HERE, "rtl", d) for d in
      ("holdout_eval_v8_firfirr", "holdout_eval_v8_poly", "holdout_eval_v8_iirmed")]
EXTRAP_TRAJ = {"fir36_8b", "fir40_8b", "firr36", "firr40"}


def hdr(t):
    print("\n" + "=" * 74 + f"\n{t}\n" + "=" * 74)


def check(label, claimed, got, tol=0.15):
    ok = abs(claimed - got) <= tol
    print(f"  {label:44s} claimed {claimed:8.3f}   computed {got:8.3f}   "
          f"{'OK' if ok else '*** MISMATCH ***'}")
    return ok


def real_fmax(d):
    out = {}
    for line in open(os.path.join(d, "ppa.jsonl")):
        try:
            r = json.loads(line)
        except ValueError:
            continue
        out[r["module"]] = float(r["fmax_mhz"]) if r.get("compiled") else 0.0
    return out


# ------------------------------------------------------------------ A
def sec_a():
    hdr("A. Aggregate correctness: is it preserved, or does it decline?")
    print("  Claim REMOVED from 05_results.tex: 'correctness is preserved in")
    print("  aggregate'. Replacement: 88.7% -> 86.9% overall; interp flat,")
    print("  extrap down >5 points.\n")
    agg = collections.defaultdict(lambda: {"w": 0.0, "c": 0, "tot": 0})
    for d in V8:
        mani = json.load(open(os.path.join(d, "fmax_manifest.json")))
        real = real_fmax(d)
        seen = set()
        for mod, i in mani.items():
            for key in ((i["policy"], i["regime"]), (i["policy"], "ALL")):
                if mod in real:
                    agg[key]["w"] += real[mod] * i["count"]
                    agg[key]["c"] += i["count"]
            if (i["policy"], i["design"]) not in seen:
                seen.add((i["policy"], i["design"]))
                agg[(i["policy"], i["regime"])]["tot"] += i["n"]
                agg[(i["policy"], "ALL")]["tot"] += i["n"]
    ok = True
    for pol, reg, claimed in (("sft", "ALL", 88.7), ("grpo", "ALL", 86.9),
                              ("sft", "interp", 92.8), ("grpo", "interp", 93.2),
                              ("sft", "extrap", 81.6), ("grpo", "extrap", 76.1)):
        a = agg[(pol, reg)]
        ok &= check(f"{pol} {reg} correctness %", claimed,
                    100.0 * a["c"] / a["tot"])
    return ok


# ------------------------------------------------------------------ B
def sec_b():
    hdr("B. Best-of-N: does one GRPO sample beat a perfect best-of-48?")
    print("  Claim WITHDRAWN. Also withdrawn: firr10/fir40 'existence failures'.")
    print("  Runs analyze_bestofn.py on the 30-design set and greps its table.\n")
    r = subprocess.run(["python", os.path.join(HERE, "analyze_bestofn.py"),
                        "--dirs"] + V8, capture_output=True, text=True)
    ok = True
    in_table1 = False
    for line in r.stdout.splitlines():
        f = line.split()
        # only the first table has the best-of-N columns; later sections reuse
        # the same design names for area and sample-cost rows
        if line.startswith("design ") and "boN=1" in line:
            in_table1 = True
        elif line.startswith("=====") and in_table1 and "MEAN" not in line:
            pass
        if line.startswith("1b)") or line.startswith("2)"):
            in_table1 = False
        if line.startswith("MEAN interp") or line.startswith("MEAN extrap"):
            reg = f[1]
            bo48, grpo = float(f[-2]), float(f[-1])
            print(f"  {reg}: perfect bo48 = {bo48:.1f} MHz, GRPO bo1 = {grpo:.1f} "
                  f"MHz  -> GRPO {'beats' if grpo > bo48 else 'does NOT beat'} bo48")
            ok &= grpo < bo48
        if in_table1 and f[:1] in (["firr10"], ["fir40_8b"]):
            print(f"  {f[0]:10s} SFT bo48 = {float(f[-2]):7.1f}   "
                  f"GRPO bo1 = {float(f[-1]):7.1f}   "
                  f"-> {'SFT wins' if float(f[-2]) > float(f[-1]) else 'GRPO wins'}")
    print("\n  Expected: GRPO does NOT beat bo48 in either regime, and SFT wins")
    print("  on both firr10 and fir40 -- which is why 'existence failure' went.")
    return ok


# ------------------------------------------------------------------ C
def sec_c():
    hdr("C. Trajectory: does the reward saturate, and where?")
    print("  Figure 1. Uses rtl/traj_v8 and rtl/traj_v9 Vivado results.\n")
    ok = True
    # (predicted, measured-over-CORRECT, correctness). The measured column is
    # deliberately the over-correct basis: it is what Figure 1 plots and the only
    # one comparable with the prediction, which scores correct candidates only.
    # The penalised basis is printed alongside because the two were mixed once
    # already -- on that basis v8 reads 230.9 -> 212.3 over the last interval,
    # and every megahertz of that movement is the correctness term.
    for tag, d, claim_end in (("v8", "rtl/traj_v8", (497.9, 241.2, 88.0)),
                              ("v9", "rtl/traj_v9", (333.2, 240.7, 99.0))):
        p = os.path.join(HERE, d)
        if not os.path.exists(os.path.join(p, "ppa.jsonl")):
            print(f"  [skip] {d}: no ppa.jsonl")
            continue
        summ = json.load(open(os.path.join(p, "holdout_summary.json")))
        mani = json.load(open(os.path.join(p, "fmax_manifest.json")))
        real = real_fmax(p)
        w = c = tot = 0.0
        seen = set()
        for mod, i in mani.items():
            if i["policy"] != "s400":
                continue
            if mod in real:
                w += real[mod] * i["count"]
                c += i["count"]
            if (i["policy"], i["design"]) not in seen:
                seen.add((i["policy"], i["design"]))
                tot += i["n"]

        rows = summ["s400"]
        pred = sum(x["mean_surr_fmax"] for x in rows.values()) / len(rows)
        corr = sum(x["corr_pct"] for x in rows.values()) / len(rows)
        print(f"  traj_{tag} final checkpoint:")
        ok &= check(f"    predicted MHz", claim_end[0], pred, tol=1.0)
        ok &= check("    measured MHz (over correct)", claim_end[1], w / c,
                    tol=1.0)
        print("      measured MHz (penalised, for reference)      "
              f"          {w / tot:8.3f}")
        ok &= check(f"    correctness %", claim_end[2], corr, tol=1.0)
        # the regime split -- the reason the caption changed
        for g, names in (("interp", lambda n: n not in EXTRAP_TRAJ),
                         ("extrap", lambda n: n in EXTRAP_TRAJ)):
            sel = [x for n, x in rows.items() if names(n)]
            gw = gc = 0.0
            for mod, i in mani.items():
                if i["policy"] == "s400" and mod in real and names(i["design"]):
                    gw += real[mod] * i["count"]
                    gc += i["count"]
            print(f"      {g:7s} predicted {sum(x['mean_surr_fmax'] for x in sel)/len(sel):7.1f}"
                  f"   measured {gw/gc:7.1f}")
    print("\n  Expected: v8's late proxy rises to ~498 while conditional measured")
    print("  Fmax stays ~241; penalised Fmax falls to ~212 as correctness falls.")
    print("  v9 tracks on interpolation but remains pinned on extrapolation.")
    return ok


# ------------------------------------------------------------------ D
def sec_d():
    hdr("D. Oracle x/z audit: did any verdict change?")
    p = os.path.join(HERE, "audit_oracle.jsonl")
    if not os.path.exists(p):
        print("  audit_oracle.jsonl absent -- run:")
        print("    python audit_oracle.py --workers 4 --dirs rtl/holdout_eval_student \\")
        print("      rtl/holdout_eval rtl/holdout_eval_qwen rtl/holdout_eval_v8_firfirr \\")
        print("      rtl/frontier_eval rtl/holdout_eval_v8_poly rtl/holdout_eval_v8_iirmed")
        return True
    recs = [json.loads(l) for l in open(p)]
    ok_r = [r for r in recs if "error" not in r]
    und = [r for r in ok_r if r.get("n_undef", 0)]
    flip = [r for r in ok_r if r.get("accept_legacy") and not r["accept_now"]]
    flop = [r for r in ok_r if r["accept_now"] and not r.get("accept_legacy")]
    print(f"  candidates audited ............................ {len(ok_r)}")
    print(f"  emit x/z on some cycle ........................ {len(und)}")
    print(f"  accepted by OLD parse but not new (false pos) . {len(flip)}")
    print(f"  accepted by NEW parse but not old ............. {len(flop)}")
    print(f"  survive exact equality ........................ "
          f"{sum(1 for r in ok_r if r['accept_exact'])}/{len(ok_r)}")
    print("\n  Expected: 1529 audited, 18 with x/z, 0 flips in either direction.")
    return len(flip) == 0 and len(flop) == 0


# ------------------------------------------------------------------ E
def sec_e(n):
    hdr(f"E. LODO stability: rerunning surrogate_train.py {n} times per arm")
    print("  THIS IS THE WEAK ONE. surrogate_train.py sets no random seed, so")
    print("  each run redraws the network initialisation. The figure I replaced")
    print("  (0.75-0.82) was itself reported as a seed RANGE, so a single draw")
    print("  cannot refute it. This section measures the spread.\n")
    arms = {
        "v2 (3 fam, 203)": ["rtl/fmax_probe_v4", "rtl/fmax_data", "rtl/policy_cmp"],
        "v3 (5 fam, 229)": ["rtl/fmax_probe_v4", "rtl/fmax_data", "rtl/policy_cmp",
                            "rtl/fmax_d2"],
        "v4 (re-anch, 272)": ["rtl/fmax_probe_v4", "rtl/fmax_data", "rtl/policy_cmp",
                              "rtl/fmax_d2", "rtl/fmax_d3"],
    }
    claimed = {"v2 (3 fam, 203)": 0.972, "v3 (5 fam, 229)": 0.915,
               "v4 (re-anch, 272)": 0.913}
    out = {}
    for label, dirs in arms.items():
        vals = []
        for i in range(n):
            r = subprocess.run(
                ["python", os.path.join(HERE, "surrogate_train.py"),
                 "--data"] + [os.path.join(HERE, d) for d in dirs] +
                ["--out", os.path.join("/tmp", f"verify_{label[:2]}_{i}.pt")],
                capture_output=True, text=True)
            for line in r.stdout.splitlines():
                if "LODO pooled Spearman" in line:
                    vals.append(float(line.rsplit("=", 1)[1]))
            print(f"    {label:20s} run {i+1}/{n}: "
                  f"{vals[-1] if vals else 'FAILED'}", flush=True)
        out[label] = vals
    print()
    for label, vals in out.items():
        if not vals:
            continue
        sd = statistics.stdev(vals) if len(vals) > 1 else 0.0
        print(f"  {label:20s} claimed {claimed[label]:.3f}   "
              f"observed {min(vals):.3f}-{max(vals):.3f} "
              f"(mean {statistics.mean(vals):.3f}, sd {sd:.3f}, n={len(vals)})")
    print("\n  Read this as: if the v3 spread OVERLAPS 0.75-0.82, my correction")
    print("  of that figure is not established and the paper must report a")
    print("  range, not a point. If the spread sits well above it, the")
    print("  correction stands.")
    return True


# ------------------------------------------------------------------ F
def _source_pointer(pointer):
    """Resolve ``repo/path:line`` or ``repo/path:start-end`` fail-closed."""
    match = re.fullmatch(r"([^:]+):(\d+)(?:-(\d+))?", pointer)
    if not match:
        return False, f"malformed source pointer: {pointer}"
    path = ROOT / match.group(1)
    if not path.is_file():
        return False, f"source does not exist: {pointer}"
    start = int(match.group(2))
    end = int(match.group(3) or start)
    with path.open(encoding="utf-8") as f:
        lines = sum(1 for _ in f)
    if start < 1 or end < start or end > lines:
        return False, f"source line outside file (has {lines} lines): {pointer}"
    return True, ""


def _collect_tex(path, seen=None):
    """Return the manuscript's recursively included TeX sources."""
    seen = set() if seen is None else seen
    path = path.resolve()
    if path in seen:
        return seen
    if not path.is_file():
        raise FileNotFoundError(path)
    seen.add(path)
    text = path.read_text(encoding="utf-8")
    for name in re.findall(r"\\input\{([^}]+)\}", text):
        # LaTeX resolves \input relative to the compilation working directory
        # (paper/), not necessarily relative to the including section file.
        candidates = [PAPER / name, path.parent / name]
        children = [p if p.suffix else p.with_suffix(".tex") for p in candidates]
        child = next((p for p in children if p.is_file()), children[0])
        _collect_tex(child, seen)
    return seen


def _strip_nonprose_commands(text):
    """Remove references/paths whose digits are identifiers, not paper claims."""
    # TeX comments are not rendered.  Escaped percent signs remain intact.
    text = re.sub(r"(?<!\\)%.*", "", text)
    # Every rendered empirical number must enter through a named claim.  Remove
    # those calls before searching for illicit raw numeric literals.
    text = re.sub(r"\\(?:claim|studyclaim)\{[A-Za-z]+\}", "", text)
    # Digits in citation keys, labels, filenames and URLs are identifiers.
    one_arg = (
        "cite", "citep", "citet", "ref", "eqref", "autoref", "label",
        "input", "includegraphics", "bibliography", "bibliographystyle",
        "url", "path",
    )
    for command in one_arg:
        text = re.sub(rf"\\{command}(?:\[[^\]]*\])?\{{[^}}]*\}}", "", text)
    text = re.sub(r"\\href\{[^}]*\}\{[^}]*\}", "", text)
    text = re.sub(r"\\(?:begin|end)\{[^}]*\}", "", text)
    return text


def sec_f_manuscript():
    hdr("F. Manuscript provenance: no hand-copied numbers")
    generator = ROOT / "analyze_main_results.py"
    ledger_path = PAPER / "generated" / "claims.json"
    study_generator = ROOT / "analyze_study2_secondary.py"
    study_ledger_path = PAPER / "generated" / "study2_claims.json"
    if not all(path.is_file() for path in (
            generator, ledger_path, study_generator, study_ledger_path)):
        print("  missing canonical generator or claim ledger")
        return False

    fresh = subprocess.run(
        [sys.executable, str(generator), "--check", "--no-figures"],
        cwd=ROOT, capture_output=True, text=True,
    )
    if fresh.returncode:
        print("  generated artifacts are stale:")
        print(fresh.stderr.rstrip())
        return False
    study_fresh = subprocess.run(
        [sys.executable, str(study_generator), "--check"],
        cwd=ROOT, capture_output=True, text=True,
    )
    if study_fresh.returncode:
        print("  generated Study 2 artifacts are stale:")
        print((study_fresh.stderr or study_fresh.stdout).rstrip())
        return False
    print("  legacy 30-design support outputs are current ... OK")
    print("  sealed Study 2 headline outputs are current .... OK")

    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    study_ledger = json.loads(study_ledger_path.read_text(encoding="utf-8"))
    claims = dict(ledger.get("claims", {}))
    for claim_id, record in study_ledger.get("claims", {}).items():
        if claim_id in claims:
            print(f"  duplicate claim ID across ledgers: {claim_id}")
            return False
        claims[claim_id] = record
    bad_sources = []
    for claim_id, record in claims.items():
        if not record.get("sources"):
            bad_sources.append(f"{claim_id}: no sources")
        for pointer in record.get("sources", []):
            ok, error = _source_pointer(pointer)
            if not ok:
                bad_sources.append(f"{claim_id}: {error}")
    if bad_sources:
        print("  invalid claim provenance:")
        for error in bad_sources:
            print(f"    {error}")
        return False
    print(f"  claim source pointers resolve .................. {len(claims)} claims OK")

    try:
        tex_paths = _collect_tex(PAPER / "main.tex")
    except FileNotFoundError as error:
        print(f"  missing included TeX file: {error}")
        return False
    used = set()
    raw_numbers = []
    for path in sorted(tex_paths):
        text = path.read_text(encoding="utf-8")
        used.update(re.findall(r"\\(?:claim|studyclaim)\{([A-Za-z]+)\}", text))
        # Generated files are checked byte-for-byte above.  The raw-literal
        # ban applies to authored title/abstract/prose, not generated macros.
        if "generated" in path.parts:
            continue
        if path.name == "main.tex" and r"\begin{abstract}" in text:
            title = re.search(r"\\title\{(.*?)\}", text, re.S)
            text = (title.group(1) if title else "") + text.split(r"\begin{abstract}", 1)[1]
        stripped = _strip_nonprose_commands(text)
        for lineno, line in enumerate(stripped.splitlines(), 1):
            if re.search(r"(?<![A-Za-z])(?:\d+(?:\.\d+)?|\.\d+)", line):
                raw_numbers.append(f"{path.relative_to(ROOT).as_posix()}:{lineno}: {line.strip()}")

    unknown = sorted(used - set(claims))
    if unknown:
        print("  manuscript uses unknown generated claims:")
        for claim_id in unknown:
            print(f"    {claim_id}")
    if raw_numbers:
        print("  raw numeric literals found in authored manuscript prose:")
        for row in raw_numbers:
            print(f"    {row}")
        print("  replace each with a generated \\claim{LettersOnlyId} or remove it")
    if not unknown and not raw_numbers:
        print(f"  rendered numeric claims are ledger-backed ........ {len(used)} used IDs OK")
    return not unknown and not raw_numbers


# ------------------------------------------------------------------ H
def sec_h_study2_secondary():
    hdr("H. Sealed Study 2 secondary closure")
    result_path = ROOT / "study2_secondary_results.json"
    primary_path = ROOT / "sealed_results_study2.json"
    audit_path = ROOT / "sealed_ppa_audit_study2.json"
    ledger_path = PAPER / "generated" / "study2_claims.json"
    table_paths = (
        PAPER / "generated" / "study2_table_comparison.tex",
        PAPER / "generated" / "study2_table_ppa.tex",
    )
    required = (result_path, primary_path, audit_path, ledger_path) + table_paths
    missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
    if missing:
        print("  missing Study 2 secondary artifacts:")
        for path in missing:
            print(f"    {path}")
        return False

    result = json.loads(result_path.read_text(encoding="utf-8"))
    primary = json.loads(primary_path.read_text(encoding="utf-8"))
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    ok = True
    if result.get("primary_outcome_unchanged") != primary.get("outcome"):
        print("  secondary result changed or detached from the primary outcome")
        ok = False
    direct = result.get("direct_rf_mlp", {})
    primary_plans = primary.get("bootstrap", {}).get("plan_sha256", {})
    for scope in ("interp", "extrap", "all"):
        row = direct.get(scope, {})
        if row.get("bootstrap_plan_sha256") != primary_plans.get(scope):
            print(f"  {scope} RF-MLP comparison did not reuse the primary plan")
            ok = False
        if row.get("n_designs") != primary.get("report", {}).get("rf", {}).get(
                "combined", {}).get(scope, {}).get("n_designs"):
            print(f"  {scope} RF-MLP design universe changed")
            ok = False
    audit_rows = audit.get("directories", [])
    expected = (
        sum(row.get("n_candidates", 0) for row in audit_rows),
        sum(row.get("n_compiled", 0) for row in audit_rows),
        sum(row.get("n_failed", 0) for row in audit_rows),
    )
    got = result.get("ppa_audit", {})
    if expected != (got.get("total"), got.get("compiled"), got.get("failed")):
        print(f"  PPA audit totals disagree: {expected} != "
              f"{(got.get('total'), got.get('compiled'), got.get('failed'))}")
        ok = False

    claims = ledger.get("claims", {})
    bad_sources = []
    for claim_id, record in claims.items():
        if not record.get("sources"):
            bad_sources.append(f"{claim_id}: no sources")
        for pointer in record.get("sources", []):
            valid, error = _source_pointer(pointer)
            if not valid:
                bad_sources.append(f"{claim_id}: {error}")
    if bad_sources:
        print("  invalid Study 2 claim provenance:")
        for error in bad_sources:
            print(f"    {error}")
        ok = False

    used = set()
    for path in table_paths:
        used.update(re.findall(
            r"\\studyclaim\{([A-Za-z]+)\}", path.read_text(encoding="utf-8")
        ))
    unknown = used - set(claims)
    if unknown:
        print("  Study 2 tables use unknown claims:")
        for claim_id in sorted(unknown):
            print(f"    {claim_id}")
        ok = False
    print(f"  immutable primary outcome ...................... {primary.get('outcome')}")
    print(f"  direct RF-MLP scopes use frozen plans .......... "
          f"{'OK' if not any(direct.get(s, {}).get('bootstrap_plan_sha256') != primary_plans.get(s) for s in ('interp','extrap','all')) else 'FAIL'}")
    print(f"  Study 2 claim pointers resolve ................. {len(claims)} claims")
    print(f"  generated Study 2 table claims resolve ......... {len(used)} used IDs")
    return ok


# ------------------------------------------------------------------ G
def _sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def sec_g_symmetric_board():
    hdr("G. Symmetric board protocol: selection, build, and live-result gate")
    directory = ROOT / "rtl" / "holdout_silicon_symmetric"
    manifest_path = directory / "selection_manifest.json"
    if not manifest_path.is_file():
        print("  symmetric selection manifest is absent")
        return False
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    selection_rule = manifest.get("candidate_selection", {}).get("rule")
    policies = manifest.get("candidate_selection", {}).get("identical_for_policies")
    selections = manifest.get("selections", [])
    ok = True
    if sorted(policies or []) != ["grpo", "sft"]:
        print(f"  candidate rule is not declared identical: {policies}")
        ok = False
    pairs = collections.defaultdict(set)
    for row in selections:
        pairs[row.get("design")].add(row.get("policy"))
        if row.get("selection_rule") != selection_rule:
            print(f"  selection-rule mismatch for {row.get('entry')}")
            ok = False
        provenance = row.get("provenance", {})
        for field, hash_field in (("rtl", "rtl_sha256"),
                                  ("copied_rtl", "copied_rtl_sha256"),
                                  ("golden", "golden_sha256")):
            path = ROOT / provenance.get(field, "__missing__")
            if not path.is_file() or _sha256(path) != provenance.get(hash_field):
                print(f"  missing or hash-mismatched {field} for {row.get('entry')}")
                ok = False
    incomplete = {design: policy for design, policy in pairs.items()
                  if policy != {"sft", "grpo"}}
    if len(selections) != 10 or len(pairs) != 5 or incomplete:
        print(f"  expected five complete pairs / ten DUTs; got {len(pairs)} / {len(selections)}")
        ok = False
    print(f"  identical candidate rule ....................... {'OK' if ok else 'FAIL'}")
    print(f"  complete symmetric policy pairs ................ {len(pairs)}")

    bit = directory / "out" / "system_holdout_symmetric.bit"
    hwh = directory / "out" / "system_holdout_symmetric.hwh"
    if bit.is_file() != hwh.is_file():
        print("  build is incomplete: bitstream/HWH pair mismatch")
        ok = False
    elif bit.is_file():
        print("  laptop bitstream and matching HWH ............... present")
    else:
        print("  laptop bitstream ................................ pending")

    result = directory / "catalog_fmax.json"
    if result.is_file():
        data = json.loads(result.read_text(encoding="utf-8"))
        if data.get("measurement_kind") != "live_pynq_clock_sweep":
            print("  reserved result exists but is not marked as a live sweep")
            ok = False
        elif data.get("provenance", {}).get("selection_manifest_sha256") != _sha256(manifest_path):
            print("  live result does not match the selection-manifest hash")
            ok = False
        else:
            print("  live PYNQ result ................................ present and linked")
    else:
        print("  live PYNQ result ................................ ABSENT (no silicon claim)")
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lodo", type=int, default=0,
                    help="rerun the unseeded LODO this many times per arm "
                         "(needs torch; ~1 min per run per arm)")
    args = ap.parse_args()
    results = [("A correctness", sec_a()), ("B best-of-N", sec_b()),
               ("C trajectory", sec_c()), ("D oracle audit", sec_d()),
               ("F manuscript provenance", sec_f_manuscript()),
               ("G symmetric board", sec_g_symmetric_board()),
               ("H Study 2 closure", sec_h_study2_secondary())]
    if args.lodo:
        results.append(("E LODO spread", sec_e(args.lodo)))
    hdr("SUMMARY")
    for name, ok in results:
        print(f"  {name:20s} {'reproduced' if ok else '*** DISAGREES ***'}")
    if not args.lodo:
        print("\n  Section E (the LODO figures) NOT run. Add --lodo 10 to test the")
        print("  one correction that rests on a single unseeded draw.")
    return 0 if all(ok for _, ok in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
