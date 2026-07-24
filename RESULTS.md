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
- **sft_v6c (5 families, D2):** train-competence probe overall **94.8%** (n=16/design); median W solved via compact `med_sort` (6.2→35.4→**89.6%**), IIR 96%+, FIR/poly canaries unchanged. Held-out evidence still pending (grpo_v8 → 30-design eval → Vivado).

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

## 2b. Best-of-N curves: one GRPO sample ≈ 48 perfectly-selected SFT samples ✅

Exact expected best-of-N (i.i.d., closed form) from the existing eval
artifacts, assuming a PERFECT selector (upper-bounds surrogate top-1 or any
reranker). `analyze_bestofn.py` → rtl/holdout_eval/bestofn.json:

| regime (mean, real MHz) | bo1 | bo8 | bo16 | bo32 | bo48 | **GRPO bo1** |
|---|--:|--:|--:|--:|--:|--:|
| Interpolation | 60.7 | 135.2 | 171.5 | 198.6 | 207.8 | **222.6** |
| Extrapolation | 47.3 | 109.2 | 133.8 | 152.3 | 159.5 | **150.0** |

- Interp: **a single GRPO sample beats a perfect selector over 48 SFT
  samples.** Extrap: one GRPO sample ≈ perfect best-of-32.
- Existence failures sampling can't fix: SFT never emits the fast form in 48
  samples for firr10 (bo48 = 68.9 vs GRPO 306.8) or fir40 (bo48 = 20.9 vs
  GRPO 181.8) — distribution shift, not selection.
- fir40 sample-cost: GRPO p(correct)=0.167 → expected **6.0 one-second oracle
  sims** to a correct 181.8 MHz design; SFT is 75% correct there but its best
  of all 48 samples is 20.9 MHz.
- Area (F7 resolved): GRPO is *smaller* in LUTs on fir (e.g. fir40 1079→788)
  paying only pipeline FFs; poly maps to DSPs (sft 5–7 → grpo +1); DSP column
  now in every table.

## 2c. HLS baseline (D1) — LLM ≈ expert HLS, ≫ naive HLS ✅

Vitis HLS on the same held-out designs, C++ kernels with oracle-exact integer
semantics, real post-P&R clock (`export_design -flow impl`), throughput =
Fmax/II. 16/22 designs (6 poly variants dropped to a Windows export-path limit;
redundant — 3 poly-degree structures already covered). `collect_hls.py`:

| variant | II | throughput (Msample/s) |
|---|--:|--:|
| naive HLS (nopragma) | tap-count / degree (fir40=134, poly=31–35) | 1.7–10.5 |
| **expert HLS** (pipeline II=1 + unroll + partition) | 1 | 195–258 |
| **GRPO (our RTL, NL spec)** | 1 | 181–346 |

- **geomean GRPO / expert-HLS throughput = 0.96×** — from a natural-language
  spec, the policy matches hand-tuned-pragma HLS to within 4% (and *exceeds*
  it on small designs: fir6 1.3×, firr6 1.4×).
- **vs naive HLS: 20–150×.** Without pragmas HLS can't pipeline the MAC/Horner
  recurrence (II = tap-count/degree), so a naive user gets single-digit
  Msample/s. The harder the recurrence (poly Horner II=31–35), the worse naive
  HLS does — the LLM emits the II=1 form directly.
- Framing: HLS input is engineer-written C++ with hand-placed pragmas; ours is
  an NL spec. The comparison bounds quality — it does not replace it.

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

## 7b. Qwen held-out MONEY TABLE (real Vivado) ✅ — the method transfers

Second base model (Qwen2.5-Coder-7B), same corpus/trainer/oracle, real
timing-closed Vivado Fmax, n=48/design, oracle seeds 1&2 n=1024:

| regime | base | sft | best-of-8 | **grpo** | grpo vs sft |
|---|--:|--:|--:|--:|--:|
| Interpolation (14) | 26.0 | 97.6 | 153.0 | **232.9 MHz** | **+139%** |
| Extrapolation (8) | 20.9 | 62.7 | 136.5 | **190.1 MHz** | **+203%** |

- grpo **beats best-of-8 in BOTH regimes** (232.9 > 153.0; 190.1 > 136.5) —
  distribution shift beats sampling on a second model.
- **Both base models converge to the SAME real-Vivado ceiling**: Qwen grpo
  232.9 / 190.1 vs RTLCoder grpo 234.4 / 190.1 (interp / extrap). The final
  Fmax is base-model-independent.
- **GRPO repairs Qwen's weak poly family**: poly7 correctness 29–54% (sft) →
  **85–100%** (grpo), and fast (32–98 → 191 MHz) — competence repair, not just
  speed. firr18 standout: sft 44.6 → grpo 243.9 MHz.
- Honest correctness cost: **firr10 92→52%, fir36 94→50%** (two designs traded
  correctness for speed; all other fir/firr/poly held ≥94%).

## 7c. Frontier-API baseline — DeepSeek-V4-Flash (correctness done, Fmax pending 🔄)

30 held-out designs × 8 samples × 2 arms (apiplain / apifast), same oracle
(seeds 1&2 n=1024). Flash (non-thinking) is strong on FIRR (62–100%), moderate
on FIR (25–37%), near-zero on held-out poly/IIR/median. Explicit maximize-Fmax
prompting did NOT improve correctness. 120 distinct-correct .sv emitted.
**Caveats before any claim:** (1) fairness — Flash tier, non-thinking, prompt
tuned to our local models; the Pro+thinking ladder (flash_nt/pro_nt/pro_think)
is required before "a frontier model can't do this"; (2) no Fmax yet — needs
laptop run_ppa on rtl/frontier_eval; (3) n=8 is noisy. No Fmax conclusion is
valid until Vivado.

## 8. Qwen second-model pipeline ✅ (complete)

sft_qwen ✅ (68.1%) → grpo_qwen ✅ → held-out eval ✅ → real Vivado ✅ →
Qwen money table (§7b): interp +139%, extrap +203%, grpo > best-of-8, same
Fmax ceiling as RTLCoder. The correctness-gated Fmax method transfers across
base models.

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
