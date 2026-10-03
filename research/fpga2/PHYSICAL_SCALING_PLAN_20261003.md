# Plan: scaling laws for the physical quality of LLM-generated hardware — 2026-10-03

**Status:** proposed direction, not a result.  Written after Gate 0 ended with
outcome B and the supervisor rejected the narrower "Goodhart in silicon" idea.
Novelty was checked on 2026-10-03 by our own searches and by independent checks
with two other models; every work cited below was verified to exist.  Supervisor
sign-off is pending.  No experiment of this plan has run.  It supersedes the
[RTL-student plan](RTL_STUDENT_PLAN_20261001.md) as the next execution target
and reuses its tools ([`student/`](../../student/README.md)).

## 1. The idea

Academic groups, EDA vendors and chip startups now train LLMs to write RTL,
sometimes with reinforcement learning (RL) on PPA rewards.  Scaling laws tell
practitioners how to spend on model size, data and compute when the target is
loss or pass rate.  No one has measured how the **physical quality of the
hardware these models generate** scales.

This study measures it with one failure-aware endpoint, the submitted paper's
failure-penalized post-route frequency `F = q·μ` (`q` = fraction of draws
correct, `μ` = multiplicity-weighted frequency of the correct ones, failures
scored zero).  Five axes are varied in a controlled way within one model family:

1. **Model size `N`.**
2. **Supervised data `D`:** the number of verified examples, and the coverage
   of implementation styles.
3. **RL compute `C`:** policy updates, against best-of-k selection at matched
   cost.
4. **Feedback fidelity:** the physical signal used as reward, from learned proxy
   through logic synthesis, FPGA post-route, ASIC post-synthesis and post-route
   to measured silicon.  This includes whether gains learned with cheap feedback
   transfer to expensive targets.
5. **Deployment compression** of the generator: FP16, GPTQ-4 and GPTQ-3.

**Outputs:**
- fitted relationships, or identified ceilings, for correctness `q` and
  correct-circuit frequency `μ` separately;
- a train-fidelity × evaluation-fidelity transfer matrix with the cost of each
  label;
- iso-cost comparisons: a bigger model, more RL, or more samples with physical
  selection;
- a released dataset of every generated circuit, with its oracle verdict and
  implementation reports.

**Why it is not narrow:** the question applies to every team that trains a
hardware-generating model, and the answer sets its budget: how big a model, how
much and which data, how much RL, and which EDA feedback (tool licences and CPU
hours).

**Why we can do it:** the submitted paper and Gate 0 already established and
audited the measurement contract (two-stream oracle, multiplicity, failure-penalized
post-route endpoint, sealed splits, frozen sampler).  We also already have the
physical-reward RL method, the circuit-dedup and Vivado pipeline, and the
PYNQ-Z2 clock-sweep harness.

**Relation to the original objective:** this is a contribution to how chips are
designed by AI, not a new neural block or accelerator.  The FFN screens, Gate 0
and the literature audits (master reference §2 and the RTL-student plan) indicate
that a new-block paper is unlikely to be defensible at a CCF-A venue with four
V100s.

## 2. What the evidence so far implies

- **Compression axis is probably flat at W4.** Gate 0 (outcome B): GPTQ-4 left
  generated-circuit frequency unchanged for the 1.5B student and the 7B SFT/RL
  pair; compression cost correctness, not physical quality.  This axis is
  therefore a short, cheap section, and it allows 4-bit deployment claims.
- **A ceiling on `μ` from the SFT data is plausible.** RL concentrates
  probability on circuits the SFT policy already emits: under GPTQ-4 the RL
  policy stays on its FP16 majority circuit for 83% of correct draws, and
  inverse-Simpson support is 0.71 against 2.04 for SFT.  The submitted paper
  reached the same reading.  Hypothesis: `μ` is bounded by the implementation
  styles reachable from the SFT data, not by model size.
- **Size matters for correctness in this domain.** The 1.5B student fails the
  median family entirely (0/16 per probe design) while the 7B handles it, so the
  size axis carries signal at least in `q`.
- **The spread is known but unexplained.** Fu et al. (2026) report large
  differences in post-synthesis quality across 32 off-the-shelf models (three
  quality tiers), but their models differ in family, data and training at once,
  so the spread cannot be attributed to any factor.

## 3. Novelty audit (2026-10-03)

**Claim to defend:** *the first controlled scaling study of the physical quality
of LLM-generated hardware, varying model size, data, RL compute, feedback
fidelity (FPGA → ASIC → silicon) and compression within one model family, under
a failure-aware post-route endpoint.*

| Work (verified) | What it does | How this study differs |
|---|---|---|
| [Fu et al., "Synthesis-in-the-Loop Evaluation of LLMs for RTL Generation" (GLSVLSI 2026)](https://arxiv.org/abs/2603.11287) | 32 off-the-shelf models on 202 tasks; hardware quality index from post-synthesis area, delay and warnings (Nangate45); three quality tiers | **Main competitor; cite it first.** Their comparison is across models, which confounds size with family, data and training.  It stops at post-synthesis and has no training axis, no fidelity or transfer, and no failure-penalized post-route endpoint. |
| [ScaleRTL](https://arxiv.org/abs/2506.05566); VeriReason (Qwen2.5 1.5B/3B/7B, GRPO); [RTLSeek](https://arxiv.org/abs/2603.27630) | Scale reasoning data, test-time compute, model size or RL | Functional pass rates only |
| [DeepCircuitX](https://arxiv.org/abs/2502.18297) | Repository-level dataset; models from 220M to 16B; PPA prediction | Predicts the PPA of given RTL; does not measure the PPA of generated RTL against scale |
| [Sun et al., multi-fidelity DSE (DATE 2021)](https://www.cse.cuhk.edu.hk/~byu/papers/C114-DATE2021-MultiFidelity.pdf); MasterRTL (ICCAD 2023) | Correlate cheap and expensive PPA estimates for exploration and prediction | Cite for the fidelity axis.  No generator is trained at each fidelity, and transfer of learned gains is not tested. |
| [Gao et al., reward-model overoptimization scaling laws (ICML 2023)](https://arxiv.org/abs/2210.10760) | Proxy versus gold reward as a policy optimizes; synthetic gold reward model | Conceptual precedent for the fidelity axis; our "gold" is real post-route timing and silicon |
| [From LLM to Silicon: RL-driven ASIC architecture exploration (2026)](https://arxiv.org/abs/2604.07526) | Scaling fits for ASIC architecture parameters across process nodes | About chip parameters versus node, not AI-model scale |
| ["Configuration Over Selection" (2026)](https://arxiv.org/abs/2604.17102) | Decoding settings change RTL quality more than model choice | A threat to any scaling claim.  It is answered by the frozen sampler plus a temperature sensitivity check (§5). |
| [COEVO](https://arxiv.org/abs/2604.15001), ChipSeek (ACL 2026), PPA-RTL (DAC 2025), VeriOpt, VeriAgent, FinHardBench | PPA-aware generation or evaluation | Single sizes or uncontrolled backbones; no scaling axis.  FinHardBench's reported cross-flow correlation (ρ = 0.982) has not been checked in the paper; check it before citing. |
| "OpenChipBench" power-area scaling law | Reported by one AI model | **Not found; do not cite.** |

**Residual risk:** searches cannot prove that something has not been done.
Before each submission, re-run Google Scholar and arXiv checks with the queries
"scaling law Verilog PPA", "physical quality generated RTL model size", "FPGA ASIC
transfer LLM RTL reward" and "LLM hardware generation post-route scaling".
Watch for a controlled-scaling follow-up by the Fu et al. group, which is the
most likely competitor.

## 4. Research questions and hypotheses

The hypotheses are directions to test, not expected results.  A smooth law and a
ceiling are both reportable outcomes.

| RQ | Question | Hypothesis |
|---|---|---|
| RQ1 size | How do `q`, `μ` and `F` change with `N` (0.5B–7B, optionally 14B) under one SFT recipe? | H1: `q` rises with `N`; `μ` changes little |
| RQ2 data | Does `μ` follow the number of examples or the implementation styles they cover? | H2: `q` rises with rows; `μ` tracks the fastest style present in the SFT data |
| RQ3 RL compute | How do `μ` and `F` grow with RL updates at each size, and how does RL compare with best-of-k selection and with a bigger model at matched cost? | H3a: `μ` grows roughly with log(updates) up to a support ceiling.  H3b: a small RL-trained model beats a larger SFT-only model in `F` at lower total cost. |
| RQ4 fidelity | Does higher-fidelity reward buy more target-level quality per unit cost, and do gains transfer FPGA → ASIC → silicon? | H4a: cheap proxies are over-optimized (proxy reward keeps rising while post-route `F` peaks).  H4b: FPGA-trained gains transfer to ASIC with the same sign and smaller size, in proportion to the cross-rung rank correlation on the policy's own circuits. |
| RQ5 compression | Does Gate 0's result hold at every size? | H5: GPTQ-4 preserves `F` at every size; 3-bit breaks small models first |

**Unique to this study:** the decomposition into `q` and `μ`.  Functional
scaling (`q`) has prior work; how the physical quality of the correct circuits
(`μ`) scales does not.

## 5. Measurement contract

| Element | Definition |
|---|---|
| Endpoint | Per design `d`: `q_d`, `μ_d`, `F_d = q_d·μ_d` (the submitted paper's Eq. 6–7); the design mean of `F` is primary.  `μ` contrasts use the common support (designs where every compared arm has a correct draw).  Secondary: LUT, FF and DSP counts and area-normalized frequency.  ASIC: cell area, WNS-derived frequency, and vectorless power labelled as an estimate. |
| Fitting split | The Gate 0 development split (20 designs, five families): all fitting, tuning and selection |
| Confirmation split | Drawn in Phase 0 with a new seed and committed by hash.  It excludes the sealed split, the dev split, every corpus design and every measured design, and every new corpus excludes it.  Untouched until Phase 5. |
| Public slice | The frozen 8-task RTLLM v2.0-era slice already audited in the previous project (`external_rtllm_slice_v1`, with official oracles and a contamination report) |
| Sampler | Frozen as in Gate 0: 24 draws per design, temperature 1.0, batch 4, generation seed 1001, stop at `endmodule`, per-family token budgets.  Sensitivity check: temperature 0.2 and 0.6 at two sizes. |
| Oracle | Two streams × 1,024 vectors; a draw is correct only if both pass |
| FPGA flow | Primary: Vivado 2023.1, `xc7z020clg400-1`, 5.0 ns request (`run_ppa.py`).  Identical RTL is implemented once and reused, with a cache keyed by the hash of the normalized RTL (as in `gate0_physical.py`). |
| Models | Qwen2.5-Coder **base** 0.5B, 1.5B, 3B, 7B; 14B on two GPUs if Phase 2 needs a wider range.  Base rather than Instruct avoids size-dependent post-training.  The family's technical report describes the same code pretraining corpus for all sizes; check this before writing it in the paper.  The 3B weights carry a research-only licence.  Second family in Phase 4: Qwen3 0.6B–8B (needs transformers ≥ 4.51). |
| SFT recipe | Fixed across sizes: `sft_train_v2.py` settings (LoRA r=16 on q/k/v/o, loss masked to the completion, 4 epochs, effective batch 16, cosine schedule), FP16 on V100.  Learning rate per size from {5e-5, 1e-4, 2e-4}, chosen on held-out *training-family* designs, never on the dev split.  LoRA-rank sensitivity (r=64) at two sizes. |
| RL recipe | The submitted paper's physical-reward method and RF reward, pinned to the commit used for its RF runs.  The same reward form at every fidelity rung (correctness gate × normalized frequency). |
| Statistics | Paired design bootstrap stratified by family × regime (10,000 resamples), plus the unstratified sensitivity interval.  Training seeds: 3 at ≤1.5B, 2 at 3B and 7B, 1 at 14B.  Seed and design variance are reported separately. |
| Fits | Pre-registered per phase.  Candidate forms: constant; log-linear; saturating power law `y = y∞ − A·x^(−α)`.  Selection by leave-one-level-out error.  Extrapolation test: fit the smaller levels and write the prediction for the largest level, with its interval, into the protocol before measuring it.  With four or five levels, claims hold only within the measured range. |
| Cost accounting | Measured GPU-hours per run; FLOPs estimated as 6·N·tokens for training and 2·N·tokens for generation; CPU-seconds per label for each EDA rung |
| Discipline | Each phase is frozen in a protocol file before its outcomes exist, with dated amendments, as for Gate 0 |

## 6. Experimental design per axis

| Axis | Arms | Sizes | Seeds | Notes |
|---|---|---|---|---|
| Size (SFT) | Full corpus (`sft_corpus.jsonl`: 534 oracle-verified rows, 152 designs, five families plus cordic, all styles) | 0.5, 1.5, 3, 7B (+14B) | 3/3/2/2 (+1) | Kill test K1 (§8) |
| Data quantity | {1/8, 1/4, 1/2, 1, 2, 4} × the corpus, with family × style proportions fixed; extra rows from `gen_sft_corpus.py` | All levels at 0.5–3B; {1/4, 1, 4} at 7B | 2 (1 at 7B) | Check the generator can supply about 2,100 distinct rows without touching the dev or confirmation splits |
| Style coverage | Per family: slowest style only; all styles except the fastest; all styles.  Row count fixed. | 1.5B (+7B at the two extremes) | 2 | Corpus styles: fir/firr {ref, unrolled, pipe, transposed}, poly {ref, inline, pipe}, iir {ref, transposed}, med {sort, comb, pipe, pipe2} |
| RL compute | RF-reward RL from each size's SFT checkpoint; evaluate at updates {0, 35, 70, 138, 276} | 0.5, 1.5, 3, 7B | 2 | Best-of-k (k = 1…24) with physical selection, computed from the same SFT draws with no new generation |
| RL beyond the data | RL from the style-limited SFT checkpoints | 1.5B | 2 | Does RL find styles missing from the SFT data?  Tests H2 and H3a together. |
| Feedback fidelity | Reward rungs R0–R5 (R6 if throughput allows), 276 updates; evaluate every policy at R4, R6 and an R7 subset; proxy and target curves over updates | 1.5B; R1 against R4 repeated at 7B if 1.5B shows a difference | 2 (1 at 7B) | Rungs below |
| Compression | FP16, GPTQ-4, GPTQ-3 at each size's SFT and final RL checkpoints | All | — | Gate 0 tools, no training |
| Generality | Off-the-shelf Qwen2.5-Coder-Instruct 0.5–14B (no training) on the RTLLM slice with FPGA and ASIC flows; Qwen3 size check at full data; ASIC rung on every Phase 2 endpoint | — | — | A pure size axis outside our generated domain |

**Feedback-fidelity rungs** (cost per label measured in Phase 0):

| Rung | Signal | Status |
|---|---|---|
| R0 | Correctness only (oracle pass) | Exists (paper control) |
| R1 | Learned proxy: random forest on structural features (the paper's reward) | Exists |
| R2 | Yosys FPGA mapping (`synth_xilinx`, LUT-6 depth and count), seconds per label | To build |
| R3 | Vivado post-synthesis timing estimate | To build (variant of `run_ppa.py`) |
| R4 | Vivado post-route timing (primary flow) | Exists |
| R5 | ASIC post-synthesis: Yosys + ABC, OpenSTA, Nangate45 | To build |
| R6 | ASIC post-route: OpenROAD flow scripts, Nangate45 (sky130hd as a check) | To build; reward use only if throughput allows |
| R7 | Silicon: PYNQ-Z2 clock sweep | Exists (board harness); evaluation subset of about 100 circuits only |

Phase 3 starts with a cheap step: rank correlations between rungs on circuits we
already hold (the 382 Gate 0 circuits plus the Phase 2 circuits).  This predicts
which rungs are worth RL runs.  R1 against R4 is run in any case.

## 7. Phases, gates and timeline

| Phase | Dates | Work | Gate or output |
|---|---|---|---|
| 0 Infrastructure | 2026-10-05 → 10-16 | Weights; server-side Vivado, Yosys and OpenROAD; EDA throughput; confirmation split; recipe provenance; K1 protocol and tools | **Hard gate:** server Vivado 2023.1 must reproduce the laptop's results on 20 Gate 0 circuits, and the per-rung throughput must be recorded.  Otherwise the study scales down (§10). |
| 1 Kill test K1 | 10-19 → 11-06 | SFT at four sizes; dev split; Vivado | Decision rule in §8 |
| 2 Scaling core | 11-09 → 12-23 | Size × data grid; style coverage; RL-compute ladder; best-of-k; compression | Frozen interim analysis.  Decide whether 14B and the second family are needed. |
| 3 Fidelity and transfer | 2027-01-04 → 02-12 | Cross-rung correlations; RL per rung; transfer matrix; silicon subset | Spring Festival (6 Feb 2027) leaves about one week of buffer |
| 4 Generality | 02-15 → 03-19 | RTLLM slice; Qwen3; ASIC flow throughout | — |
| 5 Confirmation and writing | 03-22 → mid-May | Test the pre-registered predictions on the confirmation split; write the paper; release the dataset | Submission (§11) |

## 8. Kill test K1 (draft; frozen in its own protocol before any SFT)

**Question:** under one recipe, does the physical endpoint change with model size
beyond seed noise?

**Setup:**
- Qwen2.5-Coder base 0.5B, 1.5B, 3B and 7B, each fine-tuned on `sft_corpus.jsonl`
  after a leak check against the dev and confirmation splits.
- Learning rate per size from the sweep; seeds 3/3/2/2 (10 adapters).
- Evaluation on the dev split with the frozen sampler, the oracle and the primary
  Vivado flow.

**Draft decision rule:**

| Outcome | Condition | Action |
|---|---|---|
| Trend | `F(7B) − F(0.5B)` has a paired design × seed bootstrap interval that excludes zero, and seed-mean `F` is monotone in `N` or has at most one inversion whose interval includes zero | Proceed to Phase 2 with the scaling framing |
| Ceiling | `q` follows the trend rule, but `μ` on the common support varies by less than 5% across sizes and every interval includes zero | Proceed, led by the ceiling mechanism.  Phase 2 prioritizes style coverage and RL. |
| Saturated | Every size reaches `q` ≥ 95% on the dev split | Re-plan with harder regimes and the public slice as the primary evaluation |
| No signal | All pairwise intervals for `q`, `μ` and `F` include zero, and the between-size SD of seed means is at most the within-size seed SD | Drop the scaling framing; fall back to the fidelity-transfer study alone (Phase 3), sized for DAC or TCAD |

**Cost:** about 15 GPU-hours of SFT plus about 15 for the learning-rate sweep,
about 15 GPU-hours of generation, and about 400–600 Vivado implementations.

## 9. Budget (estimates from the previous project's measurements)

**Measured anchors:**
- 1.5B SFT on 407 rows × 4 epochs: 25 min; 7B: about 3 h.
- RF-reward RL at 7B class, 276 updates: 7.8–9.1 V100-hours.
- Gate 0: 18 evaluations produced 382 distinct correct circuits.

| Item | GPU-hours | EDA implementations |
|---|---:|---|
| Size and data grid (SFT) | ≈ 50 | — |
| Evaluation of grid checkpoints (≈ 54) | ≈ 65 | ≈ 2,000 FPGA |
| RL-compute ladder (8 runs) plus checkpoint evaluations (≈ 40) | ≈ 85 | ≈ 1,500 FPGA |
| Fidelity runs (≈ 12) plus evaluations | ≈ 45 | RL labels by rung (measured in Phase 0); ≈ 2,000 ASIC post-route for evaluation |
| Compression, generality, sensitivity | ≈ 30 | ≈ 1,500 FPGA + ASIC |
| **Total** | **≈ 275** | **≈ 5,000 FPGA, ≈ 3,000 ASIC, plus RL-in-the-loop labels** |

275 GPU-hours is about four weeks of the four V100s at realistic utilization.
The EDA volume is the binding constraint: one laptop cannot produce it, so
server-side EDA is the Phase 0 hard gate.  RL with post-route reward in the loop
depends on caching.  The submitted paper found that RL policies collapse onto
few circuits, which keeps the number of unique labels small; this is to be
measured.

## 10. Risks and mitigations

| Risk | Mitigation |
|---|---|
| EDA throughput (the largest practical risk) | Run Vivado 2023.1 and open-source flows on the servers' CPUs; RTL-hash cache; parallel workers.  If the servers cannot run Vivado: the open-source FPGA rung (R2) becomes the bulk label, with Vivado on a calibrated subset and fewer arms. |
| Only four or five sizes (14×, or 28× with 14B) | Claim relationships within the range only; extrapolation test; second family |
| Narrow domain (five generated DSP families) | RTLLM slice; off-the-shelf size axis on public tasks; ASIC flow |
| Recipe confounds (fixed LoRA rank, learning rate) | Per-size learning rate on training-side validation; rank sensitivity |
| Decoding confound | Frozen sampler plus temperature sensitivity |
| Small evaluation set (20 designs) | Paired design bootstrap; training seeds; confirmation split |
| Noisy or slow EDA reward in the RL loop | Deterministic flows, timeouts scored as failures, caching |
| Overlap with the submitted TCAD paper | New claims only (scaling, fidelity, transfer); cite the paper, anonymized where review is double-blind; no text reuse |
| A competitor publishes first | Run K1 within three weeks; post a preprint after the first submission where the venue allows it |

## 11. Venues

Check the current CCF list and each call for papers; the dates below are typical
and unverified.

- **Primary: NeurIPS 2027 main track** (CCF-A; deadline usually mid-May).
  Scaling studies are welcome there, and the plan finishes in time.
- **Backups:** AAAI 2028 (CCF-A, about August 2027), DAC 2028 (CCF-A, about
  November 2027), or an extended IEEE TCAD article (CCF-A journal).  If the main
  track does not fit, the dataset can go to the NeurIPS Datasets and Benchmarks
  track.
- **DAC 2027** (November 2026) is too early for anything beyond K1.

## 12. Code to build (reusing `student/`)

| File | Purpose |
|---|---|
| `scaling/corpus.py` | Stratified data-quantity and style-coverage corpora; extra rows through `gen_sft_corpus.py`; leak check against the dev, confirmation and sealed splits |
| `scaling/train_sft.py` | Wrapper around `sft_train_v2.py` with FP16 on V100, seed, recipe hash and training record |
| `scaling/ladder.py` | `prepare`/`work`/`status` launcher (like `gate0.py`) over a job table: train → evaluate (`eval_compressed.py`) → collect |
| `scaling/eda_queue.py` | Shared-filesystem EDA job queue and cache keyed by normalized-RTL hash, with one worker type per rung; used by evaluation and the RL reward |
| `scaling/rewards.py` | Rung adapters for the RL trainer with one reward form |
| `scaling/fit.py` | Pre-registered fits, leave-one-level-out, extrapolation, bootstraps |
| Tests | CPU tests for each, as for Gate 0 |

## 13. Immediate next steps (Phase 0 checklist)

1. **Server inventory** on both boxes: CPU cores, RAM, free disk, OS and glibc,
   and whether ModelScope, PyPI mirrors or GitHub are reachable.
2. **Weights:** Qwen2.5-Coder base 0.5B, 1.5B, 3B, 7B and 14B, from ModelScope on
   the server if it is reachable, otherwise downloaded on the workstation and
   copied with scp.  Record SHA-256 for every weight file.
3. **Vivado 2023.1 on the servers:** preferred route is a WSL2 install on the
   laptop of the free Standard edition, with only Zynq-7000 (and Zynq
   UltraScale+) devices, packed with tar and copied over.  Calibrate it by
   implementing 20 Gate 0 circuits and comparing with the laptop's results.
4. **Open-source EDA:** Yosys from the OSS CAD Suite tarball; OpenROAD flow
   scripts with Nangate45 and sky130hd, from an exported container root
   filesystem run with `chroot` if the containers permit it; one design end to
   end.
5. **Throughput benchmark:** circuits per hour per rung with N parallel jobs.
6. **Confirmation split:** draw it, freeze it and commit its hash.
7. **Recipe provenance:** the exact SFT and RL scripts and commits behind
   `student_v1_out`, `sft_qwen_out`, `grpo_qwen` and the paper's RF runs, and
   whether they trained in FP16 or emulated BF16 on V100 (`sft_train_v2.py`
   requests BF16).
8. **K1:** write and freeze the K1 protocol; build the `scaling/` tools and their
   CPU tests.
