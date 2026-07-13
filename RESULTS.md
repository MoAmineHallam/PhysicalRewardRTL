# RESULTS.md — every headline number on one page

One-page consolidated results (details + provenance for each: MASTER_REFERENCE.md).
Status date: 2026-07-13. ✅ = final measured result. 🔄 = running/pending.

## 1. Competence: SFT warm-start works (and transfers) ✅

Oracle correctness (probe_competence, n=16/design, corpus-format prompts):

| model | base | after SFT | fir | firr | poly | cordic |
|---|--:|--:|--:|--:|--:|--:|
| RTLCoder-7B (sft_v5) | 6.9% | **74.4%** (93.0% non-cordic) | 87.5% | 100% | 96.9% | 0% |
| Qwen2.5-Coder-7B (sft_qwen) | 1.9% | **68.1%** (85.2% non-cordic) | 100% | 96.9% | 43.8% | 0% |

- Same corpus (358 clean pairs), same trainer, zero code changes → the recipe transfers.
- cordic = 0% on BOTH models: 7B capability-class ceiling (documented negative, kept out of RL).

## 2. THE MONEY TABLE — held-out real-Vivado verdict (Phase B core) ✅

22 frozen held-out designs (never in corpus/GRPO/surrogate), n=48/design,
oracle seeds 1&2 n=1024, real timing-closed Vivado Fmax (freq-weighted means):

| regime | base | sft_v5 | best-of-8 | **grpo_v7** | grpo vs sft | grpo vs bo8 |
|---|--:|--:|--:|--:|--:|--:|
| Interpolation (14 designs) | 35.1 | 66.5 | 113.9 | **234.4 MHz** | **+252%** | 2.06× |
| Extrapolation (8 designs) | 15.2 | 52.0 | 112.2 | **190.1 MHz** | **+265%** | 1.69× |

Correctness: interp sft 91.1% → grpo **94.6%** (holds+rises); extrap sft 89% →
grpo 78.5% (cost concentrated in fir36 65%, fir40 17%, firr40 58%; poly extrap 98–100%).

Mechanism (per-candidate data): SFT emits the fast form ~1-in-5..13 samples
(firr10: 0-in-13); GRPO emits it near-deterministically. Best-of-8 MISSED the
fast form on 6 designs → RL beats fast-tail sampling, not just cheaper.

## 3. Surrogate + gaming case study ✅

- surrogate_v2: 203 labelled pairs, LODO Spearman **0.965**, top-1 **23/25**.
- Gaming: GRPO drove poly4 to surrogate **+inf** (pilot) / 460–500 claims (v7);
  clamp [5,500] contained it; real Vivado ceiling = 191–193 MHz. Direction was
  right (grpo poly mean ≈190 vs sft ≈45–60 real); only MAGNITUDE was gamed.

## 4. Pilot (in-distribution, Phase A) ✅

rtl/policy_cmp, real Vivado: mean Fmax sft_v4 66.9 → grpo_v6 **169.8 MHz
(+154%)**, correctness held/rose on all 8 designs. F2/F4 flaws confirmed then fixed.

## 5. VerilogEval regression control (156 problems, pass@k) ✅

| policy | compile | pass@1 | pass@5 | pass@10 |
|---|--:|--:|--:|--:|
| base | 64.7% | 32.2% | 46.2% | 51.9% |
| sft_v5 | 46.6% | 16.0% | 33.0% | 40.4% |
| grpo_v7 | 46.7% | **16.7%** | **34.2%** | **41.0%** |

**GRPO adds ZERO regression beyond SFT** (KL leash worked). SFT specialization
costs ~16pp pass@1 — reversible by construction (detachable LoRA adapter).

## 6. New-family headroom vetting (both GO) ✅

Hand-written slow/fast styles, oracle-verified, real Vivado:

| family | design | slow | fast | ratio |
|---|---|--:|--:|--:|
| IIR (real feedback) | iir4/8/12 | 93/62/52 | 188/184/188 | 2.0×/3.0×/**3.6×** |
| Median (no multipliers) | med5/med9 | 77/43 | 115/110 | 1.5×/**2.6×** |

Headroom grows with size, same signature as FIR → method not FIR-specific.
(Foothold post-SFT not yet trained — GO authorizes the catalog investment.)

## 7. SILICON MONEY TABLE (PYNQ-Z2, measured) ✅ — the headline

Board+harness validated first (clean GO: canary margin 159.1 MHz,
repeatability 0.0, silicon/STA 1.91). Then the held-out shootout — one
bitstream, 5 held-out design pairs (sft-median vs grpo-top) + canary,
3 sweep runs, **spread 0.0 MHz on every entry**:

| held-out design | SFT silicon | **GRPO silicon** | speedup |
|---|--:|--:|--:|
| fir26 (interp) | 50.0 | **125.0** | 2.50× |
| firr26 (interp) | 55.6 | **125.0** | 2.25× |
| poly7 (interp) | 76.9 | **≥200 (harness-limited)** | ≥2.60× |
| firr36 (extrap) | 40.0 | **125.0** | 3.13× |
| poly8v6 (extrap) | 58.8 | **≥200 (harness-limited)** | ≥3.40× |

**On real silicon, on never-seen designs, GRPO RTL sustains 2.3–3.4× the
measured clock of SFT RTL — in both regimes, canary-attributed.** Canary
ceiling in this bitstream = 200 MHz; two GRPO entries reach it (reported
"≥200", honest). Methodology note: same-bitstream SFT-vs-GRPO comparison =
identical conditions (fair); standalone Vivado STA is a separate table —
in-context builds differ from solo compiles (grpo fir/firr: 125 in-context
vs 193–228 standalone). Harness itself characterized: valid ≤250 MHz,
breaks at 333 (sweeps capped at 260).

## 7b. Qwen held-out (correctness done ✅, Fmax needs Vivado 🔄)

GRPO **repairs** Qwen's weak family: poly7 correctness 29–54% (SFT) →
**85–100%** (GRPO) on held-out designs, while fir/firr hold 93–100%
(dips: firr10 52%, fir36 50%). Surrogate Fmax saturated at 460–500 →
real numbers need the laptop run_ppa pass on rtl/holdout_eval_qwen.

## 8. Qwen second-model pipeline 🔄

sft_qwen ✅ (68.1%) → grpo_qwen ✅ (converged, same signature as v7) →
held-out eval 🔄 (running) → laptop Vivado → Qwen money-table row.

## 9. Honest limitations (for the paper)

1. Extrapolation correctness cost at extreme taps (fir40: 17% correct, though
   182 MHz when correct).
2. Surrogate magnitude saturation at the [5,500] clamp ceiling (ranking held).
3. SFT specialization halves VerilogEval pass@1 (adapter-detachable, reversible).
4. cordic 7B ceiling (replicated across two base models).
5. Template-bounded diversity (F6 framing): GRPO shifts probability toward
   learned styles; taps 36/40 + poly v6/v7 are the honest style-transfer test.
6. Area numbers ignore DSP mapping (F7) — Fmax claims unaffected.
7. One board / one FPGA family (PYNQ-Z2, xc7z020).
