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
oracle seeds 1&2 n=1024, real WNS-derived Vivado Fmax (freq-weighted means):

| regime | base | sft_v5 | best-of-8 | **grpo_v7** | grpo vs sft | grpo vs bo8 |
|---|--:|--:|--:|--:|--:|--:|
| Interpolation (14 designs) | 35.1 | 66.5 | 113.9 | **234.4 MHz** | **+252%** | 2.06× |
| Extrapolation (8 designs) | 15.2 | 52.0 | 112.2 | **190.1 MHz** | **+265%** | 1.69× |

Correctness: interp sft 91.1% → grpo **94.6%** (holds+rises); extrap sft 89% →
grpo 78.5% (cost concentrated in fir36 65%, fir40 17%, firr40 58%; poly extrap 98–100%).

Mechanism (per-candidate data): SFT emits the fast form ~1-in-5..13 samples
(firr10: 0-in-13); GRPO emits it near-deterministically. Best-of-8 MISSED the
fast form on 6 designs → RL beats fast-tail sampling, not just cheaper.

## 2a. THE 5-FAMILY MONEY TABLE (grpo_v8, real Vivado) ✅ — the D2 headline

30 frozen held-out designs across **5 families / 3 circuit classes**, never in
corpus/GRPO/surrogate. n=48/design, oracle seeds 1&2 n=1024, real (WNS-derived)
Vivado (freq-weighted means, 346 synthesized candidates):

| regime | base | sft_v6c | best-of-8 | **grpo_v8** | grpo vs sft | vs bo8 |
|---|--:|--:|--:|--:|--:|--:|
| Interpolation (19 designs) | 28.9 | 86.5 | 153.4 | **211.3 MHz** | **+144%** | 1.38× |
| Extrapolation (11 designs) | 16.4 | 78.5 | 159.0 | **174.2 MHz** | **+122%** | 1.10× |

**Per family (interp / extrap, sft → grpo MHz):**

| family | class | interp | extrap | verdict |
|---|---|---|---|---|
| fir + firr | MAC | 97.8 → **265.9** (+172%) | 68.1 → **188.1** (+176%) | clean win |
| poly | Horner | 44.9 → **191.3** (+326%) | 57.6 → **191.6** (+233%) | **biggest win** |
| iir | recurrence | 118.3 → 148.1 (+25%) | 120.4 → 132.6 (+10%) | consistency only |
| med | comparator net | (in iir/med rows) 34.3 → 36.2 | 22.1 → 22.8 | **no Fmax gain** |

**Mechanism, now measured per candidate:** SFT emits the fast style ~1-in-4 to
1-in-8 samples; GRPO emits it near-deterministically (e.g. fir36 sft
{17,188,23,23} → grpo {188,188,188}; poly7 sft {33,33,33,33,33,191} → grpo
{192,192,192}). GRPO **shifts probability toward the fastest style the policy
already knows** — it does not invent faster hardware. Twice it slightly exceeded
the SFT ceiling (firr10 334 vs 313; firr40 195 vs 189).

**Where the win is smaller, and why (honest):**
- **iir** already emits fast forms often post-SFT, so there is less tail to fix
  (+25%/+10%); GRPO ≈ best-of-8 there rather than beating it.
- **med** gained correctness (79→85%, 29→40%) but **no speed**: the compact
  `med_sort` style that fixed median correctness is fully combinational by
  construction, so there is no fast median style for GRPO to amplify. Its
  surrogate score of 188.6 MHz was **reward hacking** — real Vivado is 36–40
  MHz (see §3b). Reported as a correctness-only win.
- **Correctness costs**: iir9_v1 92→58%, fir40 79→52%, poly7_v1 94→77%,
  iir20 79→62%, iir16 42→35%. Gains elsewhere: fir26 79→96%, iir9 81→94%,
  med7 79→85%, med11 29→40%.
- **Best-of-8 still misses the fast form entirely** on firr40 (20.7 MHz) and
  firr10 (66.6) — existence failures sampling cannot fix.

## 2b. Best-of-N curves: one GRPO sample ≈ 22 perfectly-selected SFT samples ✅

CORRECTED 2026-08-11. The previous version of this section claimed "one GRPO
sample beats a perfect selector over 48 SFT samples". That was computed on the
OLD 22-design set and does NOT survive the frozen 30-design 5-family set. Three
of its bullet points were wrong; all are restated below. `analyze_bestofn.py`
already carries the withdrawal in its own output.

Exact expected best-of-N (i.i.d., closed form) from the existing eval
artifacts, assuming a PERFECT selector (upper-bounds surrogate top-1 or any
reranker). `analyze_bestofn.py --dirs rtl/holdout_eval_v8_{firfirr,poly,iirmed}`:

| regime (mean, real MHz) | bo1 | bo8 | bo16 | bo32 | bo48 | **GRPO bo1** |
|---|--:|--:|--:|--:|--:|--:|
| Interpolation | 79.9 | 164.2 | 191.4 | 206.6 | 210.3 | **198.7** |
| Extrapolation | 61.2 | 137.1 | 154.8 | 166.2 | 170.4 | **138.6** |

- Interp: one GRPO sample ≈ perfect **best-of-22** (198.7, between bo16=191.4
  and bo32=206.6). Extrap: ≈ perfect **best-of-8** (138.6 vs bo8=137.1).
  GRPO does NOT exceed bo48 on either regime.
- The perfect selector is unbuildable — it needs the true post-implementation
  Fmax of all N candidates, i.e. N synthesis runs — so it upper-bounds every
  real reranker. The two defensible statements are (a) at EQUAL sample count
  (1 vs 1) GRPO beats SFT 79.9→198.7 interp / 61.2→138.6 extrap, which is not a
  selection effect; and (b) one GRPO sample is worth roughly the N above of SFT
  samples judged by a selector nobody can build, hence strictly more than N
  real samples.
- GRPO bo1 exceeds SFT bo48 on 6 of 30 designs, all poly (poly7_8b 192.1 vs
  188.7; poly7_v3 191.1 vs 170.2; poly8_v6/v7 179.2 vs 170.6/170.9;
  poly7_v2 191.1 vs 188.7; poly7_v5 187.1 vs 183.9), and ties fir18 and firr26.
- WITHDRAWN — "existence failures sampling cannot fix". On the 30-design set
  SFT bo48 REACHES the fast form on both designs previously cited: firr10
  bo48 = 313.2 (vs GRPO 300.7, i.e. SFT wins) and fir40 bo48 = 181.7 (vs GRPO
  94.7, SFT wins). The old "bo48 = 20.9" for fir40 confused the SFT MEDIAN
  (20.9 MHz, correct — see the area table) with its best of 48. The fast form
  is a RARE event under SFT, not an absent one, and the honest framing is
  distribution reallocation, not existence.
- fir40 sample-cost, corrected: sft 38/48 correct (p=0.792, 1.3 expected
  oracle-checked samples to first correct, best real 181.8 MHz); grpo 25/48
  (p=0.521, 1.9 samples, best real 181.8 MHz). Identical best Fmax. fir40 is a
  design where GRPO buys nothing and costs correctness — it is one of the five
  regressions, and it sits in the extrapolation region where the reward is
  saturated (§ trajectory analysis, 2026-08-11).
- Area (F7 resolved): GRPO is *smaller* in LUTs on fir (fir40 1079→788, fir26
  655→480) paying only pipeline FFs; poly maps to DSPs (sft 3–7 → grpo +1);
  DSP column now in every table.

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

## 3b. Reward hacking: a detectable signal, and one caught case ✅ (new)

Across the 5-family held-out eval, **surrogate saturation at the [5,500] clamp
predicted correctness loss**: every large regression (iir9_v1, iir16, iir20,
poly7_v1, fir40) sat on a design whose grpo surrogate score pinned at 500, while
every design where the surrogate returned a realistic value (iir5 135, iir9 250,
med7 84) held or improved. Saturation is therefore an **observable early-warning
signal for reward hacking**.

The clearest single case: **med7 surrogate 188.6 MHz vs real Vivado 36–40 MHz.**
The surrogate (LODO Spearman 0.75 after the 5-family retrain, down from 0.965 on
3 families) had no discrimination on comparator networks and was gamed. Poly's
500-pins, by contrast, were **not** hacking — real Fmax is 191–193 MHz, i.e. the
surrogate was wrong in *magnitude* but right in *ranking*. This is the empirical
case for re-anchoring (D3) and for invariant #2: surrogate numbers are never
results.

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
WNS-derived Vivado Fmax, n=48/design, oracle seeds 1&2 n=1024:

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

## 7c. Frontier-API baseline — DeepSeek-V4-Flash, real Vivado ✅ (honest, nuanced)

30 held-out designs × 8 samples × 2 arms, same oracle (seeds 1&2 n=1024), real
Vivado. Two arms give OPPOSITE answers, and the distinction is the result:

**Arm A — `apiplain` (the EXACT prompt our models get) → we win 2–9×:**

| design | Flash plain maxF | grpo maxF | ratio |
|---|--:|--:|--:|
| fir40 | 20.7 | 181.8 | **8.8×** |
| fir26 | 32.1 | 193.2 | **6.0×** |
| firr10 | 70.4 | 313.3 | **4.4×** |
| fir6 | 155.8 | 317.6 | **2.0×** |

→ **A frontier model does not emit fast RTL by default** (20–156 MHz, the same
slow range as SFT). You have to know to ask.

**Arm B — `apifast` (explicitly "maximize Fmax, pipeline aggressively") →
Flash beats us on FIR/FIRR peak Fmax, 10 of 12 designs, by 5–30%** (fir26 251
vs 193, fir6 376 vs 318, firr10 369 vs 313; grpo still wins firr40 189 vs 183
and firr26 228 vs 217). Reported as-is — this is the mandatory-honesty arm.

**Three bounds on that win (all measured):**
1. **Coverage.** Flash fails outside FIR/FIRR: poly **0% correct on 9/10**
   designs (grpo: 191–192 MHz at ~100%), iir 0–12.5%, med 0–25%. Our policy is
   94–100% correct across all five families.
2. **Correctness rate.** Even where fast, Flash is 25–87.5% correct — and which
   samples are correct is knowable ONLY because our oracle says so. Without a
   correctness oracle a user gets fast-looking RTL that is wrong ~1 in 3.
3. **It pays in registers.** apifast fir6 = 106 LUT / **185 FF** vs our grpo 79
   LUT / **96 FF** (~2× the flops for +18% Fmax); fir40 1410 FF vs our 640 for
   +13%. Deeper pipeline = more latency and area (F7).

**Honest framing for the paper:** same prompt → our small local policy is 2–9×
faster; prompted-for-speed → a frontier API matches/exceeds us on the two
easiest families while failing the other three. The contribution is reliable,
correct, fast RTL across all five families from a local 7B, plus the oracle
that makes any such comparison measurable at all. Caveat: n=8/arm is noisy
(25% = 2/8); Pro + thinking rungs pending (API credit).

## 8. Qwen second-model pipeline ✅ (complete)

sft_qwen ✅ (68.1%) → grpo_qwen ✅ → held-out eval ✅ → real Vivado ✅ →
Qwen money table (§7b): interp +139%, extrap +203%, grpo > best-of-8, same
Fmax ceiling as RTLCoder. The correctness-gated Fmax method transfers across
base models.

## 8b. Distillation: 4 of 5 families compress to 1.5B ✅ (Phase D+)

`gen_distill_corpus.py` sampled grpo_v8 over all 145 train-split designs, keeping
only oracle-verified-correct outputs → **407 rows from 3480 samples** (1–5
distinct per design: the policy is near-deterministic, the distribution-shift
signature). Student = Qwen2.5-Coder-**1.5B**, same trainer, **25 minutes**
(vs ~3 h for the 7B), final loss 0.0395.

| probe (n=16, train designs) | base 1.5B | **student** |
|---|--:|--:|
| firr16 | 0% | **93.8%** |
| poly6 | 0% | **93.8%** |
| iir8 | 0% | **87.5%** |
| fir16 | 0% | **68.8%** |
| med3 / med5 / med9 | 0% | **0%** (compiled 10/4/5 of 16) |
| overall | 0.0% | 49.1% — **85.9% excluding median** |

**Capability-size frontier:** median works at 7B and dies at 1.5B — the
cordic-at-7B pattern one size class down. Both halves are results: silicon-grade
RTL for 4 of 5 families from a laptop-size model trained in 25 minutes, plus an
honest size limit.

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
