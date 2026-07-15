# CLAUDE.md — Project handoff: silicon-grounded RL for RTL generation

**Read this before doing anything. Do not deviate from the plan in §6 without the
user's explicit approval.** The detailed research log is `MASTER_REFERENCE.md`
(§10 = the V2 method); this file is the operational handoff: current state,
known flaws, frozen decisions, and the exact next steps.

## 1. What this project is

Fine-tune RTLCoder-7B (at `/zeng_gk/Amine/mas/rtlcoder` on the GPU server) so it
generates FPGA accelerator RTL (fir/firr/poly families) that is functionally
CORRECT (V2 oracle, I/O-equivalence) and FAST (high Fmax), with final claims
validated on real Vivado and real silicon (PYNQ-Z2). Pipeline:
oracle (Stage 0, done) → SFT warm-start (Stage 1, done) → Fmax surrogate
(Stage 3, done) → correctness-gated online GRPO (Stage 4, pilot done) →
held-out + silicon validation (pending — the paper's core).

## 2. Machines and workflow (three-box setup, git is the transfer bus)

- **Sandbox** (this environment, `/home/user/FPGA`): code authoring, numpy-only
  analysis, iverilog available. No GPU, no torch, no Vivado, no board.
- **GPU server** (`/zeng_gk/Amine/mas/fpga`, conda env `mas`): training,
  generation, oracle scoring. Its GitHub link is FLAKY (443 timeouts /
  GnuTLS -110). Recipes that work:
  `git config --global http.version HTTP/1.1`, and
  `until git fetch origin; do sleep 30; done && git reset --hard origin/claude/amazing-hopper-ytsbvr`.
  Server is a pure consumer: always `fetch + reset --hard`, never merge.
  Pushes from the server use a fine-grained PAT in the URL form.
- **Laptop** (Windows, `C:\Users\Amine\mas\fpga-repo`): Vivado 2023.1
  (`run_ppa.py --vivado "C:\Xilinx\Vivado\2023.1\bin\vivado.bat"`), board access.
- Branch: `claude/amazing-hopper-ytsbvr`. Commit as
  `user.email noreply@anthropic.com`, `user.name Claude` (a stop-hook enforces this).
- **NEVER let the user paste tokens into chat** — if it happens, tell them to
  revoke immediately (it has happened twice).

## 3. Non-negotiable invariants

1. **Only the oracle decides correctness** (`oracle.score(...)['correct']`);
   never Hamming/trace similarity (that was the V1 flaw).
2. **Surrogate numbers are never results.** The surrogate is a training-time
   reward only; every reported Fmax must come from real Vivado (`run_ppa.py`)
   or the board. The surrogate has been gamed once already (poly4 → ∞).
3. **Held-out isolation** (§5): held-out designs must never appear in the SFT
   corpus, the GRPO design list, or the surrogate's training rows. Check before
   every training run.
4. **Update `MASTER_REFERENCE.md` after every result** (positive or negative),
   with honest provenance.
5. cordic is a documented negative result (7B ceiling) — do not spend compute
   trying to rescue it; it stays out of RL.

## 4. Known flaws found in review (fix status; fix in Phase B unless noted)

- **F1 — Contamination (CRITICAL).** All results so far are in-distribution
  (training designs). Nothing yet proves generalization. Fix: the frozen
  held-out protocol in §5/§6-B. Note: an earlier claim that poly4_v2/poly8_v3
  were "unseen" was WRONG — they were in the corpus.
- **F2 — Surrogate gaming (CONFIRMED).** GRPO produced poly4 RTL the surrogate
  scores as ∞ (exp overflow), and firr8 at 441–566 "MHz" (above any real value).
  Fix: clamp predicted log-Fmax to [ln 5, ln 500] in surrogate load AND in the
  GRPO reward; after Phase A synthesis, add the gamed designs with their real
  Vivado labels to surrogate training (re-anchor) and retrain.
- **F3 — GRPO KL anchors to the BASE model, not the SFT policy.**
  `grpo_oracle.py` uses `use_adapter=False` (= base) as the KL reference while
  the policy starts from the SFT adapter — so the KL mildly pulls the policy
  AWAY from SFT competence. Damage was small (kl≈0.05) but fix for v7: keep a
  frozen copy of the SFT adapter as reference (peft multi-adapter: load SFT
  twice, one frozen "ref" + one trainable "policy"; compute ref logprob under
  the frozen adapter).
- **F4 — Generation budget truncates large designs (explains fir32).**
  fir32/firr32 transposed ≈ 750+ tokens; GRPO/probe caps were 768 → truncated
  mid-module → extraction fails → zero reward → policy learns to avoid the fast
  form. Fix: `--max-tokens 1536` everywhere (GRPO, probes, eval). SFT-side:
  the >2048 warnings were cordic-only (harmless to RL), but train v5 with
  `--max_length 4096` after confirming `config.max_position_embeddings ≥ 4096`
  (RTLCoder is deepseek-coder-based, 16k context; tokenizer's 2048 is a
  misconfigured default).
- **F5 — Same-stimulus overfitting risk.** Training reward and all evals used
  oracle seed=0, n=512. A policy could in principle overfit the exact vectors.
  Fix: final evals score with seed=1 AND seed=2, n=1024; training keeps seed=0.
- **F6 — Template-bounded diversity (framing risk).** SFT completions are
  template-generated; GRPO shifts probability among learned styles rather than
  inventing novel ones. The paper must claim "shifts the generation
  distribution toward high-Fmax implementation styles and generalizes across
  parameters", not "invents fast designs". The extrapolation held-outs
  (taps 36/40) are the honest test of style generalization.
- **F7 — Area numbers ignore DSPs.** Vivado maps multiplies to DSP blocks
  (that's why some rows show lut=1). Either report DSP counts too or drop area
  claims; Fmax claims are unaffected.
- **F8 — GRPO gradient includes post-endmodule junk.** Reward is computed on
  the extracted module but logprob on the whole sampled sequence. Minor noise;
  for v7 truncate `gen_ids` at the first "endmodule" token span.
- **F9 — Single-seed, n=24 evals.** For the money tables use n=48/design and,
  if time allows, 2 sampling seeds; report means (CIs if feasible).
- **F10 — GRPO trained on only 8 prompts.** v7 must train on ALL train-split
  designs (dozens of prompts), which also reduces per-prompt overfitting.

## 5. FROZEN held-out split (decided — do not change)

Held-out = excluded from SFT corpus, GRPO design list, and surrogate training
rows. Evaluation happens ONLY here (plus VerilogEval for regression).

- **Interpolation:** fir taps {6, 10, 18, 26} (`fir6_8b`, `fir10_8b`,
  `fir18_8b`, `fir26_8b`); firr taps {6, 10, 18, 26}; poly degree 7 (all
  variants: `poly7_8b`, `poly7_v1..v5_8b`).
- **Extrapolation (outside trained range):** fir taps {36, 40}; firr {36, 40};
  poly NEW variants v6, v7 of degrees {4, 8} (`poly4_v6_8b`, `poly4_v7_8b`,
  `poly8_v6_8b`, `poly8_v7_8b`) — `GAC.poly_coeffs_var` and the oracle already
  handle any (deg, v) by name, and `GAC.fir_coeffs(T)` any T.
- Train split = everything else: fir/firr taps 4..32 minus {6,10,18,26}, poly
  degrees {2..10}\{7} × v0..v5. Cordic stays in the corpus (14 pairs) but out
  of RL.
- Eval prompts for held-out designs cannot come from `gen_sft_corpus.designs()`
  after the regen (they won't be yielded) — build them directly:
  `GSC.make_prompt(GAC.fir_spec(nm,T), GAC.fir_ref(nm,c))` etc. (the interface
  header is part of the problem statement, not leakage).
- **D2 families (frozen 2026-07-13, BEFORE sft_v6/grpo_v8 ever trained):**
  iir train grid = orders 2..14 × variants v0..v3 (styles ref/transposed);
  med train grid = W {3,5,9} (styles comb/pipe/pipe2; med11+ exceeds the
  1536-token gen budget, F4, so it is the extrap point, eval'd at 3072 tokens).
  - Interpolation: iir orders {5, 9} (all variants); med W {7}.
  - Extrapolation: iir orders {16, 20}; med W {11}.
  `GSC.is_holdout()` covers them; eval adds iir5/iir5_v1/iir9/iir9_v1/med7
  (interp) + iir16/iir20/med11 (extrap) → 30 eval designs total.

## 6. Execution plan — PATH A (revised 2026-07-13 with explicit user approval)

**Target venues: ACM FPGA / FCCM / MLCAD — NOT DAC.** Three independent harsh
external reviews converged: the RL method is incremental vs the
VeriReason/ChipSeek-class 2025 work by DAC standards, but the
silicon-validated evaluation + honest held-out protocol is a strong fit
(est. 50–70%) at FPGA/FCCM/MLCAD. Consequences, frozen:
- Title/scope claims **"DSP accelerator RTL"**, never general RTL generation.
- Phrase as **silicon-VALIDATED** (post-hoc measurement), never
  silicon-in-the-loop — the board does not participate in training.
  Stage-2 vector player stays future work.

### DONE (numbers: RESULTS.md; provenance: MASTER_REFERENCE.md)
Phase A pilot ✅ (in-distribution real Vivado, +154%). Phase B ✅ (held-out
money table: interp +252% w/ corr 91.1→94.6%, extrap +265%; > best-of-8;
VerilogEval control: GRPO adds zero regression beyond SFT). Qwen SFT+GRPO ✅.
IIR+median vetted GO ✅. Board smoke test clean GO ✅ (canary margin 159 MHz,
spread 0.0, silicon/STA 1.91). SILICON MONEY TABLE ✅ (2.3–3.4× measured,
spread 0.0, canary-attributed). D1 HLS baseline ✅ (GRPO from NL spec = 0.96×
expert-HLS throughput geomean, 20–150× naive HLS). D5 analyses ✅ (exact
best-of-N: GRPO bo1 > perfect-selector bo48 interp; fir40 sample-cost; F7 DSP
columns). D2 code ✅ + sft_v6 trained ✅ (loss 0.51→0.005; probe pending).

### Phase C — finish silicon + Qwen row (IN FLIGHT)
1. Holdout shootout bitstream (`rtl/holdout_silicon`, self-checked 11/11
   match=1.0000): laptop `build_holdout.tcl` → scp kit to board →
   `sweep_catalog.py --bit system_holdout.bit --sels holdout_sels.json
   --lo 30 --hi 340 --step 5 --runs 3` → **silicon money table** (5 held-out
   designs × sft-median vs grpo-top + canary). GRPO entries may exceed the
   attributable ceiling → report "≥ canary−margin", that is honest and fine.
   Record; scp the sweep JSONs back into the repo.
2. Qwen held-out eval (running) → laptop run_ppa on `rtl/holdout_eval_qwen`
   → `eval_holdout.py --report --out-dir rtl/holdout_eval_qwen` → Qwen row.

### Phase D — reviewer-hardening (order = impact per effort)
1. **HLS baseline (BLOCKER at every venue):** C++ kernels for the 22 held-out
   designs + Vitis HLS batch script (with/without pipeline/unroll pragmas);
   compare Fmax + correctness vs GRPO. Framing: our input is an NL spec, not
   C++ — but the comparison must exist. Sandbox authors kernels+script;
   laptop runs them.
2. **Family expansion to 5 (scope BLOCKER):** promote iir/med (templates in
   vet_families.py, both vetted GO) into gen_accelerator_catalog +
   gen_sft_corpus + oracle, WITH their own frozen held-out split; regen
   corpus → sft_v6 → surrogate_v3 → grpo_v8 (5 families jointly) → extended
   held-out eval + Vivado. One model, 5 families, 3 circuit classes.
3. **Surrogate-vs-real-EDA ablation (STRONG):** partial GRPO (~50–100 steps,
   design subset) with real Vivado OOC reward vs surrogate reward + wall-clock
   cost table; fold in one surrogate re-anchor cycle (add new fast TRAIN-split
   real labels → surrogate_v3 → show top-range discrimination restored).
4. **Positioning (mandatory writing):** verify then cite VeriReason,
   ChipSeek-R1, VeriSeek, SymRTLO, RTLRewriter, CraftRTL, CodeV; delta table
   (our delta: correctness-gated Fmax objective; clamped + re-anchored
   surrogate; frozen interp/extrap protocol; canary-attributed silicon).
   Treat unverifiable "2026" citations from AI reviews as hallucinations
   until a real link exists.
5. **Cheap fixes:** DSP counts in every area table (already in ppa.jsonl, F7);
   fir40 sample-cost analysis from existing artifacts ("GRPO + oracle-check
   ≈ 6 cheap sims to a correct 182 MHz design"); cordic stays as the
   replicated-negative finding; best-of-{8,16,48} surrogate-selection curves
   computed from the EXISTING eval artifacts (isolates policy shift vs better
   sampling — zero GPU); one written paragraph on the GRPO↔DPO connection
   (full DPO baseline = rebuttal contingency only, not planned); limitation
   line: specs are template-generated NL.
6. **Framing (from 3rd review, adopt):** position as "a gold standard for
   EVALUATING LLM-generated hardware" — the narrow domain is what MAKES the
   per-design oracle+silicon rigor possible (feature, not apology). Claim
   "most rigorous/attributable silicon methodology", never "first silicon"
   (a survey reportedly counts ~1/3 of LLM-RTL projects with some FPGA check).
   Calibration note: the three external reviews scored DAC-as-is at 5%/<5%/65%
   — the 65% is the flattering outlier; venue decision stays Path A, revisit
   only after D1+D2 are complete.

### Phase D+ — distillation to a small fast model (supervisor request 2026-07-15)

Goal: compress the GRPO capability into a 1–3B student ("detachable skill",
fast + low-token inference for interactive chip design). Runs AFTER grpo_v8
frees the GPUs; does NOT gate the start of Phase-E writing.
1. **Distillation corpus (sandbox+server):** sample N per TRAIN-split design
   from the grpo_v8 policy (fallback grpo_v7), keep ONLY oracle-verified
   correct outputs (invariant #1 applies to distillation data too — the oracle
   filter is what makes our distillation unusually clean), dedup by norm().
   Held-out split stays frozen; the student must never see it (invariant #3).
2. **Student SFT:** Qwen2.5-Coder-1.5B (or deepseek-coder-1.3b); download via
   ModelScope mirror (China — hf.co is blocked; NEVER rely on hub downloads).
   Same `sft_train_v2.py`, unchanged recipe. ~1 GPU-day.
3. **Evaluate with the EXISTING harness, nothing new:** probe_competence →
   eval_holdout (seeds 1&2, n=1024) → laptop run_ppa → a student row in the
   money table. Report tokens/sec and tokens-per-correct-fast-design vs the
   7B, chained with the existing ~48× best-of-N token reduction (1 GRPO sample
   ≈ perfect-selector best-of-48 SFT samples).
4. **Either outcome is publishable:** capability compresses to 1.5B (strong
   practical claim: silicon-quality RTL from a laptop-size model) OR a
   capability-size frontier finding (families die going down in size, the
   cordic-at-7B pattern — honest negative, same as before).
5. **Engineering alternative to mention to supervisor:** int4 quantization
   (AWQ/GPTQ) + vLLM on the existing 7B gives 2–5× speedup with no research
   risk — distillation is the research answer, quantization the deploy answer.

### Phase E — write + submit
Figures: money table (Vivado + silicon, interp/extrap); mechanism CDF (SFT
fast-tail vs GRPO default); gaming case study (∞ → clamp → real 191); HLS +
best-of-N cost comparison; VerilogEval; 5-family competence; distillation /
efficiency row (7B vs student: correctness, real Fmax, tokens/s) if Phase D+
lands in time — else future-work paragraph. Limitations = RESULTS.md §9
verbatim. Venue: primary CCF-A shot = ICCAD 2027 (abstract ~early Apr 2027,
paper ~1 wk later, HotCRP, NO abstract extensions — iccad.com/2027 when live);
DAC 2027 (~Nov 2026) = earlier alternative; FPGA/FCCM/MLCAD remain the
strong-fit fallbacks per Path A. A hardened journal version can follow with
Phase-D leftovers.

## 7. Key files

`oracle.py` (V2 reward), `gen_accelerator_catalog.py` (design/style emitters:
fir_ref/fir_pipe/fir_unrolled/fir_transposed, poly_*, cordic_*),
`gen_sft_corpus.py` (corpus), `sft_train_v2.py` (SFT trainer, loss masked to
completion), `surrogate_train.py` (text-feature Fmax MLP + LODO eval),
`grpo_oracle.py` (online GRPO), `probe_competence.py` (base-vs-adapter
correctness probe; also exports `probe_prompts`/`generate`),
`gen_fmax_candidates.py` (distinct-correct candidates for Vivado),
`compare_policies.py`/`compare_eval.py` (SFT-vs-GRPO on surrogate/real Fmax),
`run_ppa.py` (laptop Vivado batch), `analyze_accel_spread.py` (headroom),
`clock_sweep_fmax.py`/`sweep_catalog.py` (board silicon Fmax),
`run_verilogeval_passk.py` (regression benchmark).
Adapters on server: `sft_v3_out`, `sft_v4_out` (current), `grpo_v6` (pilot).
Data: `sft_corpus.jsonl` (408 pairs), `rtl/fmax_data` + `rtl/fmax_probe_v4`
(151 labeled RTL→Fmax pairs), `surrogate.pt`, `rtl/policy_cmp` (pilot eval).

## 8. Current numbers (for orientation; details in MASTER_REFERENCE)

Base → SFT correctness 3.5% → 84.7% (fir/firr 100%, poly 90.6%, cordic 0%).
Fmax headroom (Vivado): median within-design spread 155 MHz. Surrogate LODO
Spearman 0.959, top-1 15/17. GRPO pilot (surrogate, in-distribution):
fir8 105→323, fir16 46→198, firr8 103→322, firr16 59→198, poly6 67→124,
correctness held/rose; poly4 gamed to ∞; fir32/poly8_v3 unimproved (F4/F10).
Real-Vivado pilot verdict: PENDING (Phase A).
