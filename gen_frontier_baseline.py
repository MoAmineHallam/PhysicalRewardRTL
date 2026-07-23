#!/usr/bin/env python3
"""
gen_frontier_baseline.py  -  Phase D: frontier-API baseline (supervisor request
2026-07-17). Answers the reviewer question "why not just prompt a big model?"

Sends the SAME held-out prompts our models get (spec + exact interface, built
by eval_holdout.holdout_designs) to an OpenAI-compatible chat API, in TWO arms:

  plain : the exact prompt our models see (tests default behaviour -- does a
          frontier model emit fast RTL unprompted?)
  fast  : plain + an explicit "maximize Fmax / pipeline aggressively" ask
          (the honest arm: what can the frontier model do when TOLD to be
          fast? Skipping this invites the reviewer to assume the best case.)

Outputs are scored by the SAME pipeline as everything else: oracle at seeds
1&2 n=1024 (F5), distinct-correct candidates emitted as .sv + fmax_manifest
for the laptop run_ppa pass, then --report prints the comparison row next to
the existing grpo/sft numbers from rtl/holdout_eval.

Setup (any OpenAI-compatible endpoint; DeepSeek shown):
  export FRONTIER_API_KEY=sk-...
  export FRONTIER_BASE_URL=https://api.deepseek.com     # default
  export FRONTIER_MODEL=deepseek-chat                   # default

  python gen_frontier_baseline.py --dry-run             # inspect prompts, $0
  python gen_frontier_baseline.py                       # ~30 designs x 8 x 2
  (laptop) run_ppa.py --dir rtl/frontier_eval --out rtl/frontier_eval/ppa.jsonl
  python gen_frontier_baseline.py --report

Resumable: a design/arm with already-emitted .sv files (or a recorded zero-
correct result) is skipped; delete rtl/frontier_eval to start over.
NEVER paste the API key into chat or commit it; env var only.
"""

import os
import json
import time
import argparse
from collections import defaultdict

import requests

import gen_sft_corpus as GSC
import eval_holdout as EH

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, os.environ.get("FRONTIER_OUT_DIR", "rtl/frontier_eval"))
EVAL = os.path.join(HERE, "rtl", "holdout_eval")
SUMMARY = os.path.join(OUT, "frontier_summary.json")

FAST_SUFFIX = (
    "\n\nIMPORTANT: optimize the implementation for MAXIMUM clock frequency "
    "(Fmax) on an FPGA. Pipeline aggressively; keep the register-to-register "
    "critical path as short as possible (e.g. one multiply and one add per "
    "stage); extra pipeline latency is acceptable and will not be penalized.")


def api_call(prompt, model, base, key, temp, max_tokens, tries=4):
    url = base.rstrip("/")
    if not url.endswith("/chat/completions"):
        url += "/chat/completions"
    body = {"model": model, "temperature": temp, "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}]}
    thinking = os.environ.get("FRONTIER_THINKING", "")
    reasoning_effort = os.environ.get("FRONTIER_REASONING_EFFORT", "high")
    if thinking:
        body["thinking"] = {"type": thinking}
        if thinking == "enabled":
            body["reasoning_effort"] = reasoning_effort
    hdr = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    for t in range(tries):
        try:
            r = requests.post(url, json=body, headers=hdr, timeout=300)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
        except Exception as e:
            if t == tries - 1:
                print(f"    [api-fail after {tries} tries] {e}")
                return ""
            time.sleep(2 ** (t + 1))
    return ""


def load_summary():
    return json.load(open(SUMMARY)) if os.path.exists(SUMMARY) else {}


def run_generation(args):
    key = os.environ.get("FRONTIER_API_KEY", "")
    base = os.environ.get("FRONTIER_BASE_URL", "https://api.deepseek.com")
    model = os.environ.get("FRONTIER_MODEL", "deepseek-chat")
    if not key and not args.dry_run:
        raise SystemExit("set FRONTIER_API_KEY (env var only -- never paste "
                         "keys into chat/commits)")

    hd = EH.holdout_designs()
    if args.families:
        keep = set(args.families.split(","))
        hd = [row for row in hd if row[1] in keep]
    if args.designs:
        keep = set(args.designs)
        hd = [row for row in hd if row[0] in keep]

    arms = [("apiplain", ""), ("apifast", FAST_SUFFIX)]
    if args.dry_run:
        nm, fam, reg, spec, ref = hd[0]
        p = GSC.make_prompt(spec, ref)
        print(f"{len(hd)} designs x {args.n} samples x 2 arms = "
              f"{len(hd) * args.n * 2} calls to {model} @ {base}")
        print(f"\n----- arm 'apiplain' prompt for {nm} -----\n{p}")
        print(f"\n----- arm 'apifast' adds -----{FAST_SUFFIX}")
        return

    os.makedirs(OUT, exist_ok=True)
    summary = load_summary()
    mani_p = os.path.join(OUT, "fmax_manifest.json")
    mani = json.load(open(mani_p)) if os.path.exists(mani_p) else {}

    for nm, fam, reg, spec, ref in hd:
        prompt0 = GSC.make_prompt(spec, ref)
        for tag, suffix in arms:
            if nm in summary.get(tag, {}):
                print(f"SKIP {tag}/{nm} (done: "
                      f"{summary[tag][nm]['corr_pct']:.0f}% correct)")
                continue
            print(f">>> {tag} / {nm}", flush=True)
            mt = max(3072, args.max_tokens) if nm == "med11" else args.max_tokens
            distinct = {}          # norm -> {"rtl", "count"}
            n_correct = 0
            for i in range(args.n):
                text = api_call(prompt0 + suffix, model, base, key,
                                args.temp, mt)
                rtl = EH.extract_verilog(text, nm) if text else None
                ok = bool(rtl) and EH.correct_both_seeds(rtl, nm, args.n_stim)
                n_correct += ok
                if ok:
                    k = EH.norm(rtl)
                    if k in distinct:
                        distinct[k]["count"] += 1
                    else:
                        distinct[k] = {"rtl": rtl, "count": 1}
                time.sleep(args.sleep)
            for j, d in enumerate(distinct.values()):
                mod = f"{tag}__{nm}__g{j}"
                open(os.path.join(OUT, mod + ".sv"), "w").write(
                    EH.rename(d["rtl"], nm, mod))
                mani[mod] = {"policy": tag, "design": nm, "count": d["count"],
                             "n": args.n, "regime": reg, "model": model,
                             "run_label": os.environ.get("FRONTIER_RUN_LABEL", ""),
                             "thinking": os.environ.get("FRONTIER_THINKING", ""),
                             "reasoning_effort": os.environ.get(
                                 "FRONTIER_REASONING_EFFORT", "")}
            summary.setdefault(tag, {})[nm] = {
                "corr_pct": 100.0 * n_correct / args.n, "n": args.n,
                "regime": reg, "model": model,
                "run_label": os.environ.get("FRONTIER_RUN_LABEL", ""),
                "thinking": os.environ.get("FRONTIER_THINKING", ""),
                "reasoning_effort": os.environ.get(
                    "FRONTIER_REASONING_EFFORT", "")}
            json.dump(mani, open(mani_p, "w"), indent=1)
            json.dump(summary, open(SUMMARY, "w"), indent=1)
            print(f"    correct {n_correct}/{args.n}, "
                  f"{len(distinct)} distinct", flush=True)

    print(f"\ndone -> {OUT}  (next: laptop run_ppa --dir rtl/frontier_eval, "
          f"then --report)")


def report():
    summary = load_summary()
    mani = json.load(open(os.path.join(OUT, "fmax_manifest.json")))
    fmax = {}
    ppa_p = os.path.join(OUT, "ppa.jsonl")
    if os.path.exists(ppa_p):
        for line in open(ppa_p):
            try:
                p = json.loads(line)
            except ValueError:
                continue
            if p.get("compiled"):
                fmax[p["module"]] = float(p["fmax_mhz"])
    # frontier per design/arm: freq-weighted mean + max real fmax
    rows = defaultdict(lambda: defaultdict(list))
    for mod, info in mani.items():
        if mod in fmax:
            rows[info["design"]][info["policy"]].append(
                (fmax[mod], info["count"]))
    # grpo/sft comparison columns from the existing held-out eval
    grpo = {}
    gm_p, gp_p = (os.path.join(EVAL, "fmax_manifest.json"),
                  os.path.join(EVAL, "ppa.jsonl"))
    if os.path.exists(gm_p) and os.path.exists(gp_p):
        gfx = {}
        for line in open(gp_p):
            try:
                p = json.loads(line)
            except ValueError:
                continue
            if p.get("compiled"):
                gfx[p["module"]] = float(p["fmax_mhz"])
        for mod, info in json.load(open(gm_p)).items():
            if info["policy"] == "grpo" and mod in gfx:
                d = info["design"]
                grpo[d] = max(grpo.get(d, 0.0), gfx[mod])

    print(f"{'design':14s} {'reg':6s} | {'plain corr%':>11s} {'maxF':>6s} | "
          f"{'fast corr%':>10s} {'maxF':>6s} | {'grpo maxF':>9s}")
    print("-" * 78)
    designs = sorted({d for arm in summary.values() for d in arm},
                     key=lambda d: (summary[next(iter(summary))][d]["regime"], d))
    for d in designs:
        reg = summary[next(iter(summary))][d]["regime"]
        cells = []
        for tag in ("apiplain", "apifast"):
            s = summary.get(tag, {}).get(d)
            corr = f"{s['corr_pct']:10.1f}" if s else "         -"
            mf = max((f for f, _ in rows[d].get(tag, [])), default=None)
            cells.append((corr, f"{mf:6.1f}" if mf else "     -"))
        g = grpo.get(d)
        print(f"{d:14s} {reg[:6]:6s} | {cells[0][0]} {cells[0][1]} | "
              f"{cells[1][0]} {cells[1][1]} | "
              f"{f'{g:9.1f}' if g else '        -'}")
    print("\nReading: 'plain' = same prompt our models get; 'fast' = "
          "explicitly asked to pipeline for Fmax.\nFrontier Fmax cells need "
          "the laptop run_ppa pass first (blank until then).")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=8, help="samples/design/arm")
    ap.add_argument("--temp", type=float, default=1.0,
                    help="match our eval protocol (1.0)")
    ap.add_argument("--max-tokens", type=int, default=3072)
    ap.add_argument("--n-stim", type=int, default=1024, help="oracle len (F5)")
    ap.add_argument("--sleep", type=float, default=0.5, help="s between calls")
    ap.add_argument("--families", default="",
                    help="comma list, e.g. 'fir,firr,poly' for the 22-design "
                         "set that matches the existing grpo_v7 eval")
    ap.add_argument("--designs", nargs="*", default=[])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args()
    if args.report:
        report()
    else:
        run_generation(args)


if __name__ == "__main__":
    main()
