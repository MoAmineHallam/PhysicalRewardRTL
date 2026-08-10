#!/usr/bin/env python3
"""
eval_holdout.py  -  Phase B held-out evaluation (the paper's generalization test).

Everything before this was in-distribution: the Phase-A verdict compared SFT vs
GRPO on designs the model TRAINED on. This evaluates ONLY the frozen §5 held-out
designs -- excluded from the SFT corpus, the GRPO design list, and the surrogate's
training rows -- so it is the honest test of whether the policy LEARNED a fast
implementation style or merely memorised the training grid. Two regimes, reported
SEPARATELY:
  * interpolation -- parameters inside the trained range, held out
      (fir/firr taps 6,10,18,26; poly degree 7, all variants);
  * extrapolation -- parameters OUTSIDE the trained range
      (fir/firr taps 36,40; poly NEW variants v6,v7 of degrees 4,8).

Four policies:
  base       -- the raw base model (adapter disabled);
  sft        -- the SFT warm-start policy (sft_v5);
  grpo       -- the correctness-gated Fmax GRPO policy (grpo_v7);
  bestof8    -- draw 8 from sft, keep the surrogate-best CORRECT one (the
                inference-cost baseline: does one GRPO sample beat 8 SFT samples?).

Correctness is the V2 oracle at seeds 1 AND 2, n=1024 (F5: training used seed 0;
a candidate counts correct only if it matches under BOTH unseen stimulus seeds,
which guards against same-stimulus overfitting). Held-out prompts are built
DIRECTLY from the catalog -- they are NOT yielded by gen_sft_corpus.designs()
after the holdout regen, so we construct spec+interface here (the interface
header is part of the problem statement, not leakage).

Distinct-correct RTL is emitted (tagged by policy, with sample multiplicity) plus
fmax_manifest.json, exactly like compare_policies, so run_ppa gives REAL Vivado
Fmax; `--report` then reads ppa.jsonl for the money table.

  server: python eval_holdout.py --sft sft_v5_out --grpo grpo_v7 \
             --surrogate surrogate_v2.pt --out-dir rtl/holdout_eval --n 48
  laptop: run_ppa.py --dir rtl/holdout_eval --out rtl/holdout_eval/ppa.jsonl \
             --clk clk --period 5.0 --vivado ...
  server: python eval_holdout.py --report --out-dir rtl/holdout_eval
"""

import os
import re
import json
import argparse
from collections import defaultdict

os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "0")

import numpy as np

import gen_accelerator_catalog as GAC
import gen_sft_corpus as GSC
import oracle
from build_dataset import extract_verilog

# oracle stimulus seeds for the correctness gate (F5). Training used seed 0; here
# we demand agreement on TWO different unseen seeds so a policy cannot win by
# overfitting the exact training vectors.
EVAL_SEEDS = (1, 2)


# ----------------------------------------------------------------- held-out set
def holdout_designs():
    """(name, family, regime, spec_text, ref_rtl) for the frozen §5 split, built
    directly. ref_rtl only supplies the module interface for the prompt (the
    oracle rebuilds the true reference from the design name)."""
    out = []
    # interpolation (params inside the trained grid, held out)
    for T in sorted(GSC.HOLDOUT_FIR_TAPS):
        nm = f"fir{T}_8b"; c = GAC.fir_coeffs(T)
        out.append((nm, "fir", "interp", GAC.fir_spec(nm, T), GAC.fir_ref(nm, c)))
    for T in sorted(GSC.HOLDOUT_FIR_TAPS):
        nm = f"firr{T}"; c = [k + 1 for k in range(T)]
        out.append((nm, "firr", "interp", GAC.firr_spec(nm, T), GAC.fir_ref(nm, c)))
    for v in range(6):                         # poly degree 7, variants v0..v5
        D = 7; nm = f"poly{D}_8b" if v == 0 else f"poly{D}_v{v}_8b"
        c = GAC.poly_coeffs_var(D, v)
        out.append((nm, "poly", "interp", GAC.poly_spec(nm, D, c), GAC.poly_ref(nm, c)))
    # extrapolation (params outside the trained grid)
    for T in sorted(GSC.HOLDOUT_EXTRAP_TAPS):
        nm = f"fir{T}_8b"; c = GAC.fir_coeffs(T)
        out.append((nm, "fir", "extrap", GAC.fir_spec(nm, T), GAC.fir_ref(nm, c)))
    for T in sorted(GSC.HOLDOUT_EXTRAP_TAPS):
        nm = f"firr{T}"; c = [k + 1 for k in range(T)]
        out.append((nm, "firr", "extrap", GAC.firr_spec(nm, T), GAC.fir_ref(nm, c)))
    for D in (4, 8):                           # poly deg 4,8 NEW variants v6,v7
        for v in sorted(GSC.HOLDOUT_EXTRAP_POLY_VARS):
            nm = f"poly{D}_v{v}_8b"; c = GAC.poly_coeffs_var(D, v)
            out.append((nm, "poly", "extrap", GAC.poly_spec(nm, D, c),
                        GAC.poly_ref(nm, c)))
    # D2 families (sft_v6/grpo_v8 runs only -- earlier adapters never saw them)
    for N in sorted(GSC.HOLDOUT_IIR_ORDERS):   # iir interp: orders 5,9 x v0,v1
        for v in (0, 1):
            nm = f"iir{N}" if v == 0 else f"iir{N}_v{v}"
            B = GAC.iir_coeffs_var(N, v)
            out.append((nm, "iir", "interp", GAC.iir_spec(nm, N, B),
                        GAC.iir_ref(nm, B)))
    for N in sorted(GSC.HOLDOUT_EXTRAP_IIR_ORDERS):   # iir extrap: 16,20 (v0)
        B = GAC.iir_coeffs_var(N, 0)
        out.append((f"iir{N}", "iir", "extrap", GAC.iir_spec(f"iir{N}", N, B),
                    GAC.iir_ref(f"iir{N}", B)))
    for W in sorted(GSC.HOLDOUT_MED_W):               # med interp: W=7
        out.append((f"med{W}", "med", "interp", GAC.med_spec(f"med{W}", W),
                    GAC.med_comb(f"med{W}", W)))
    for W in sorted(GSC.HOLDOUT_EXTRAP_MED_W):        # med extrap: W=11
        out.append((f"med{W}", "med", "extrap", GAC.med_spec(f"med{W}", W),
                    GAC.med_comb(f"med{W}", W)))
    # invariant: every eval design MUST be in the frozen held-out split
    leak = [nm for nm, *_ in out if not GSC.is_holdout(nm)]
    assert not leak, f"eval design(s) not in held-out split: {leak}"
    return out


def norm(rtl):
    """Whitespace/name-insensitive key so identical designs dedup to one .sv."""
    body = re.sub(r"\bmodule\s+\w+", "module M", rtl, count=1)
    return re.sub(r"\s+", " ", body).strip()


def rename(rtl, design, mod):
    return re.sub(r"\bmodule\s+" + re.escape(design) + r"\b",
                  "module " + mod, rtl, count=1)


def correct_both_seeds(rtl, design, n_stim):
    """Oracle correctness under BOTH unseen stimulus seeds (F5)."""
    try:
        return all(oracle.score(rtl, design, n=n_stim, seed=s)["correct"]
                   for s in EVAL_SEEDS)
    except Exception:
        return False


# ----------------------------------------------------------------- generation
def load_surrogate(path, device):
    import torch
    import torch.nn as nn
    from surrogate_train import (extract_features, LOGF_MIN, LOGF_MAX, clamp_fmax)
    ck = torch.load(path, map_location=device, weights_only=False)
    n = len(ck["feat_names"])
    net = nn.Sequential(nn.Linear(n, 32), nn.ReLU(), nn.Linear(32, 32),
                        nn.ReLU(), nn.Linear(32, 1))
    net.load_state_dict(ck["state"]); net.eval().to(device)
    mu = torch.tensor(ck["mu"], dtype=torch.float32, device=device)
    sd = torch.tensor(ck["sd"], dtype=torch.float32, device=device)
    log_target = ck.get("log_target", True)

    @torch.no_grad()
    def pred(rtl):
        x = torch.tensor(extract_features(rtl, ck["feat_names"]),
                         dtype=torch.float32, device=device)
        out = net(((x - mu) / sd).unsqueeze(0)).item()
        if log_target:
            out = min(max(out, LOGF_MIN), LOGF_MAX)      # F2: clamp then exp
            return clamp_fmax(float(np.exp(out)))
        return clamp_fmax(float(out))
    return pred


def gate_design(texts, nm, predict, n_stim):
    """Dedup samples -> distinct candidates; oracle-gate (seeds 1&2, n_stim) and
    surrogate-score each distinct once. Returns (distinct, order):
      distinct[key] = {count, rtl, correct, fmax}
      order         = per-sample key (or None if extraction failed)."""
    distinct, order = {}, []
    for t in texts:
        rtl = extract_verilog(t, nm)
        if rtl is None:
            order.append(None); continue
        rtl = rtl.encode("ascii", "replace").decode("ascii")
        key = norm(rtl)
        if key not in distinct:
            distinct[key] = {"count": 0, "rtl": rtl, "correct": False, "fmax": 0.0}
        distinct[key]["count"] += 1
        order.append(key)
    for dd in distinct.values():
        dd["correct"] = correct_both_seeds(dd["rtl"], nm, n_stim)
        dd["fmax"] = predict(dd["rtl"]) if dd["correct"] else 0.0
    return distinct, order


def summarise(distinct, n):
    """(corr%, mean surrogate Fmax, max surrogate Fmax) over CORRECT samples."""
    nc = sum(d["count"] for d in distinct.values() if d["correct"])
    fm = [d["fmax"] for d in distinct.values() if d["correct"]
          for _ in range(d["count"])]
    return (100.0 * nc / n, float(np.mean(fm)) if fm else 0.0,
            float(max(fm)) if fm else 0.0)


def emit_distinct(tag, nm, regime, distinct, n, out_dir, mani):
    """Write each distinct-correct candidate as a .sv + manifest row (run_ppa)."""
    j = 0
    for d in distinct.values():
        if not d["correct"]:
            continue
        mod = f"{tag}__{nm}__g{j}"; j += 1
        open(os.path.join(out_dir, mod + ".sv"), "w").write(
            rename(d["rtl"], nm, mod))
        mani[mod] = {"policy": tag, "design": nm, "count": d["count"],
                     "n": n, "regime": regime}


def run_generation(args):
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM
    from peft import PeftModel
    from probe_competence import generate

    os.makedirs(args.out_dir, exist_ok=True)
    hd = holdout_designs()
    if args.families:
        keep = set(args.families.split(","))
        hd = [row for row in hd if row[1] in keep]
    print(f"held-out eval: {len(hd)} designs "
          f"({sum(r=='interp' for _,_,r,_,_ in hd)} interp, "
          f"{sum(r=='extrap' for _,_,r,_,_ in hd)} extrap), "
          f"n={args.n}/design, oracle seeds {EVAL_SEEDS} n={args.n_stim}", flush=True)
    # precompute prompts (spec + exact interface header), corpus format
    # --fast-prompt appends the SAME instruction the frontier-API 'apifast' arm
    # uses, so the reviewer question "could you get this by just ASKING the SFT
    # model to be fast?" is answered on OUR model, not only on a frontier one.
    suffix = FAST_SUFFIX if args.fast_prompt else ""
    if suffix:
        print("[fast-prompt] appending the explicit maximise-Fmax instruction "
              "to every prompt (control for prompt engineering)", flush=True)
    prompts = [(nm, fam, reg, GSC.make_prompt(spec, ref) + suffix)
               for nm, fam, reg, spec, ref in hd]

    tok = AutoTokenizer.from_pretrained(args.base)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    base = AutoModelForCausalLM.from_pretrained(
        args.base, torch_dtype=torch.float16, device_map={"": 0})
    dev = next(base.parameters()).device
    predict = load_surrogate(args.surrogate, dev)

    mani, summary = {}, {}

    def eval_adapter(tag, model):
        summary[tag] = {}
        results = {}
        print(f"\n=== {tag} ===  {'design':12s} {'corr%':>6s} "
              f"{'meanF':>7s} {'maxF':>6s}", flush=True)
        for nm, fam, reg, prompt in prompts:
            # med11's pipelined form is ~2000 tokens -- the ONE design where the
            # default 1536 cap would truncate the honest answer (F4 lesson)
            mt = 3072 if nm == "med11" else args.max_tokens
            texts = generate(model, tok, prompt, args.n, args.temp,
                             mt, batch=args.gen_batch)
            distinct, order = gate_design(texts, nm, predict, args.n_stim)
            corr, mF, xF = summarise(distinct, args.n)
            summary[tag][nm] = {"corr_pct": corr, "mean_surr_fmax": mF,
                                "max_surr_fmax": xF, "regime": reg, "n": args.n}
            emit_distinct(tag, nm, reg, distinct, args.n, args.out_dir, mani)
            results[nm] = {"distinct": distinct, "order": order, "regime": reg}
            print(f"  {nm:12s} {corr:6.1f} {mF:7.1f} {xF:6.1f}", flush=True)
        return results

    if args.trajectory:
        # Figure-1 data: proxy-vs-real divergence ALONG the optimisation path.
        # Each point is a saved checkpoint, evaluated with the SAME prompts,
        # oracle gate and emit path as the main table, so the trajectory and
        # the headline numbers are directly comparable.
        #
        # Adapters are loaded into ONE PeftModel via load_adapter/set_adapter
        # rather than re-wrapping the base model per checkpoint: wrapping an
        # already-wrapped model nests LoRA layers, and with 5+ points that is
        # both wrong and slow.
        specs = [s for s in args.trajectory.split(",") if s.strip()]
        model = PeftModel.from_pretrained(base, args.sft, adapter_name="step0",
                                          is_trainable=False).eval()
        model.set_adapter("step0")
        eval_adapter("step0", model)
        for spec in specs:
            label, path = spec.split("=", 1)
            label = label.strip()
            model.load_adapter(path.strip(), adapter_name=label,
                               is_trainable=False)
            model.set_adapter(label)
            eval_adapter(label, model)
        json.dump(mani, open(os.path.join(args.out_dir,
                                          "fmax_manifest.json"), "w"), indent=1)
        json.dump(summary, open(os.path.join(args.out_dir,
                                             "holdout_summary.json"), "w"),
                  indent=1)
        print(f"\ntrajectory candidates + manifest -> {args.out_dir}\n"
              f"next (laptop): run_ppa.py --dir {args.out_dir} ... then plot "
              f"predicted vs measured per checkpoint", flush=True)
        return

    # base FIRST (clean base_model, before any adapter is injected)
    eval_adapter("base", base)
    # sft -- keep its per-design distinct/order to derive best-of-8
    sft_model = PeftModel.from_pretrained(base, args.sft, is_trainable=False).eval()
    sft_results = eval_adapter("sft", sft_model)
    del sft_model; torch.cuda.empty_cache()
    # grpo
    grpo_model = PeftModel.from_pretrained(base, args.grpo, is_trainable=False).eval()
    eval_adapter("grpo", grpo_model)
    del grpo_model; torch.cuda.empty_cache()

    # best-of-8 derived from the sft samples (no extra generation): among the
    # FIRST args.bestof sft samples, keep the surrogate-best CORRECT one.
    tag = "bestof8"; summary[tag] = {}
    print(f"\n=== {tag} (top-surrogate of first {args.bestof} sft samples) ===",
          flush=True)
    for nm, fam, reg, _ in prompts:
        distinct = sft_results[nm]["distinct"]; order = sft_results[nm]["order"]
        window = order[:args.bestof]
        cands = [distinct[k] for k in window if k and distinct[k]["correct"]]
        if cands:
            best = max(cands, key=lambda d: d["fmax"])
            mod = f"{tag}__{nm}__g0"
            open(os.path.join(args.out_dir, mod + ".sv"), "w").write(
                rename(best["rtl"], nm, mod))
            mani[mod] = {"policy": tag, "design": nm, "count": 1,
                         "n": args.bestof, "regime": reg}
            corr = 100.0 * sum(1 for k in window if k and distinct[k]["correct"]) \
                / args.bestof
            summary[tag][nm] = {"corr_pct": corr, "mean_surr_fmax": best["fmax"],
                                "max_surr_fmax": best["fmax"], "regime": reg,
                                "n": args.bestof}
        else:
            summary[tag][nm] = {"corr_pct": 0.0, "mean_surr_fmax": 0.0,
                                "max_surr_fmax": 0.0, "regime": reg,
                                "n": args.bestof}

    json.dump(mani, open(os.path.join(args.out_dir, "fmax_manifest.json"), "w"),
              indent=1)
    json.dump(summary, open(os.path.join(args.out_dir, "holdout_summary.json"),
                            "w"), indent=1)
    print(f"\nwrote candidates + manifest + holdout_summary.json -> {args.out_dir}\n"
          f"next (laptop): run_ppa.py --dir {args.out_dir} --out {args.out_dir}/"
          f"ppa.jsonl --clk clk --period 5.0 --vivado ...\n"
          f"then (server): python eval_holdout.py --report --out-dir {args.out_dir}")


# ----------------------------------------------------------------- report
# Identical wording to gen_frontier_baseline.FAST_SUFFIX so the prompt-engineering
# control is comparable across our model and the frontier-API arm.
FAST_SUFFIX = (
    "\n\nIMPORTANT: optimize the implementation for MAXIMUM clock frequency "
    "(Fmax) on an FPGA. Pipeline aggressively; keep the register-to-register "
    "critical path as short as possible (e.g. one multiply and one add per "
    "stage); extra pipeline latency is acceptable and will not be penalized.")


POLICIES = ["base", "sft", "bestof8", "grpo"]


def run_report(args):
    mani = json.load(open(os.path.join(args.out_dir, "fmax_manifest.json")))
    sp = os.path.join(args.out_dir, "holdout_summary.json")
    summary = json.load(open(sp)) if os.path.exists(sp) else {}
    fmax = {}
    ppa = os.path.join(args.out_dir, "ppa.jsonl")
    if os.path.exists(ppa):
        for line in open(ppa):
            try:
                p = json.loads(line)
            except ValueError:
                continue
            if p.get("compiled"):
                fmax[p["module"]] = float(p.get("fmax_mhz", 0.0))
    else:
        print(f"[warn] no {ppa} yet -- run_ppa on the laptop first; "
              f"showing surrogate-only correctness columns.")

    # (policy, design) -> weighted real Fmax
    agg = defaultdict(lambda: {"wsum": 0.0, "cnt": 0, "max": 0.0})
    regime_of, designs = {}, set()
    for mod, info in mani.items():
        designs.add(info["design"]); regime_of[info["design"]] = info["regime"]
        if mod in fmax:
            a = agg[(info["policy"], info["design"])]
            a["wsum"] += info["count"] * fmax[mod]
            a["cnt"] += info["count"]
            a["max"] = max(a["max"], fmax[mod])

    def corr_of(policy, d):
        return summary.get(policy, {}).get(d, {}).get("corr_pct", float("nan"))

    def real_mean(policy, d):
        a = agg.get((policy, d))
        return (a["wsum"] / a["cnt"]) if a and a["cnt"] else 0.0

    def real_max(policy, d):
        a = agg.get((policy, d))
        return a["max"] if a else 0.0

    for regime in ("interp", "extrap"):
        ds = sorted(d for d in designs if regime_of.get(d) == regime)
        if not ds:
            continue
        title = {"interp": "INTERPOLATION (held-out, in-range)",
                 "extrap": "EXTRAPOLATION (held-out, out-of-range)"}[regime]
        print(f"\n================ {title} ================")
        head = f"{'design':12s} |"
        for p in POLICIES:
            head += f" {p+' cor/realF':>18s} |"
        print(head); print("-" * len(head))
        pol_means = defaultdict(list)
        for d in ds:
            row = f"{d:12s} |"
            for p in POLICIES:
                row += f" {corr_of(p, d):5.0f}% {real_mean(p, d):7.1f} |"
                pol_means[p].append(real_mean(p, d))
            print(row)
        print("-" * len(head))
        summ = f"{'MEAN realF':12s} |"
        for p in POLICIES:
            m = float(np.mean(pol_means[p])) if pol_means[p] else 0.0
            summ += f" {'':6s}{m:7.1f} |"
        print(summ)
        # headline deltas vs sft
        sft_m = float(np.mean(pol_means["sft"])) if pol_means["sft"] else 0.0
        for p in ("grpo", "bestof8"):
            pm = float(np.mean(pol_means[p])) if pol_means[p] else 0.0
            if sft_m > 0:
                print(f"  {p} vs sft real Fmax: {sft_m:.1f} -> {pm:.1f} "
                      f"({pm - sft_m:+.1f} MHz, {100*(pm-sft_m)/sft_m:+.0f}%)")

    print("\nVERDICT (per regime): the paper's claim holds if, on HELD-OUT designs,"
          " grpo correctness >= sft AND grpo real Fmax > sft; best-of-8 is the "
          "inference-cost baseline (one grpo sample vs 8 sft samples). Report "
          "interpolation and extrapolation separately.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=os.environ.get(
        "RTLCODER_PATH", "/zeng_gk/Amine/mas/rtlcoder"))
    ap.add_argument("--sft", default="sft_v5_out")
    ap.add_argument("--grpo", default="grpo_v7")
    ap.add_argument("--surrogate", default="surrogate_v2.pt")
    ap.add_argument("--out-dir", default="rtl/holdout_eval")
    ap.add_argument("--n", type=int, default=48, help="samples/design (F9)")
    ap.add_argument("--bestof", type=int, default=8, help="best-of-N baseline N")
    ap.add_argument("--n-stim", type=int, default=1024,
                    help="oracle stimulus length for the correctness gate (F5)")
    ap.add_argument("--temp", type=float, default=1.0)
    ap.add_argument("--max-tokens", type=int, default=1536)   # F4
    ap.add_argument("--fast-prompt", action="store_true",
                    help="append an explicit maximise-Fmax instruction to every\n                         prompt; the prompt-engineering control baseline")
    ap.add_argument("--trajectory", default="",
                    help="comma list of label=adapter_path checkpoints. Skips "
                         "base/bestof8 and evaluates the SFT start (as 'step0') "
                         "followed by each checkpoint, producing the "
                         "proxy-vs-real-over-training-steps data. Restrict the "
                         "design set with --families and lower --n to keep the "
                         "Vivado bill affordable.")
    ap.add_argument("--families", default="",
                    help="comma list to restrict eval (e.g. 'iir,med' for the "
                         "D2 extension run); empty = all held-out designs")
    ap.add_argument("--gen-batch", type=int, default=8)
    ap.add_argument("--report", action="store_true",
                    help="read ppa.jsonl + summary and print the money table")
    args = ap.parse_args()

    if args.report:
        run_report(args)
    else:
        run_generation(args)


if __name__ == "__main__":
    main()
