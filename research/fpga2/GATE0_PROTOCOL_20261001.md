# Gate 0 protocol — compression and generated-circuit quality

**Frozen 2026-10-01, before the development split was drawn and before any
generation.**  Implements Gate 0 of the [RTL-student plan](RTL_STUDENT_PLAN_20261001.md).
Code: [`student/gate0.py`](../../student/gate0.py) and the tools it calls.
Any change after this point is recorded below as a dated amendment, before the
affected outcome is seen.

## Question

Does weight quantization or output-head trimming of an RTL-generating policy
reduce the post-route frequency of its *correct* circuits (`μ`), in addition to
any loss of correctness (`q`)?

## Inputs

| Input | Definition |
|---|---|
| Frozen evaluator | Previous-project files at GitHub commit `40acc78` (`moaminehallam/fpga`). `gate0.py prepare` uses the server checkout whose `eval_sealed.py`, `oracle.py`, `grpo_oracle.py`, `build_dataset.py`, `score_candidate.py`, `gen_sealed_split.py`, `gen_sft_corpus.py`, `gen_accelerator_catalog.py` and `canonicalize.py` all match the recorded hashes, and stops otherwise. The oracle self-check must print `True`. |
| Development split | `make_dev_split.py`, seed 20261001: the frozen sealed-split generator, excluding the sealed split, every design named in any manifest or summary in the three server checkouts, and the generator's own exclusions; median extrapolation widths 23 and 25 added. Budget rule uses the Qwen2.5-Coder-1.5B tokenizer. Drawn once; its SHA-256 is stored in `gate0/plan.json` and in every run's `generation_config.json`. Never used for training or calibration. |
| Kept vocabulary | `make_keep_vocab.py`: tokens of every completion in `sft_corpus.jsonl`, `sft_corpus_v5.jsonl`, `distill_corpus.jsonl`, plus EOS/PAD and printable-ASCII tokens. |

## Policies and design families

Families are those each policy was trained on, fixed from its training records.

| Tag | Model | Adapter | Families | GPTQ calibration corpus | Box / GPU |
|---|---|---|---|---|---|
| `stu` | Qwen2.5-Coder-1.5B | `fpga/student_v1_out` | fir, firr, poly, iir (0% median at FP16) | `distill_corpus.jsonl` | V100b, arms split over both GPUs |
| `qsft` | Qwen2.5-Coder-7B-Instruct | `fpga/sft_qwen_out` | fir, firr, poly | `sft_corpus_v5.jsonl` | V100a GPU 0 |
| `qgrpo` | Qwen2.5-Coder-7B-Instruct | `fpga/grpo_qwen` | fir, firr, poly | `sft_corpus_v5.jsonl` | V100a GPU 1 |

All arms of a policy run on one GPU model, so comparisons within a policy never
mix V100 types.

## Arms

The LoRA adapter is merged into the FP16 base first; compression is applied to
the merged model, as deployed.  Quantization covers the seven decoder
projections (`q,k,v,o,gate,up,down`), symmetric, one FP16 scale per 128 inputs;
embeddings and the output head stay FP16.

| Arm | Transform | Policies |
|---|---|---|
| `fp16` | none (reference) | all |
| `rtn8`, `rtn4`, `rtn3` | round-to-nearest, 8/4/3 bits | `rtn8`: `stu` only; others all |
| `gptq4`, `gptq3` | GPTQ, 4/3 bits; decoder layers in order; 128 calibration rows rendered as in SFT, ≤2,048 tokens, seed 0; 1% damping | all |
| `fp16t` | output restricted to the kept vocabulary | `stu` |
| `gptq4t` | `gptq4` plus the kept vocabulary | `stu` |

## Sampling and correctness

24 draws per design, temperature 1.0, batch 4, generation seed 1001 for every
run, the frozen sampler (stop at `endmodule`) and per-family token budgets from
the split.  Two oracle streams of 1,024 vectors; a draw is correct only if both
pass.  Distinct correct candidates keep their multiplicity; every other draw
counts as zero.  A failed run is moved aside and rerun from scratch, never
resumed or merged.

## Physical evaluation

Every distinct correct candidate, deduplicated across all runs by normalized
RTL, is implemented once with the submitted paper's primary flow (`run_ppa.py`,
Vivado 2023.1, `xc7z020clg400-1`, 5.0 ns request).  `F(m)` is the
timing-derived frequency, zero on implementation failure.  Results are joined
back to every run that emitted the candidate.

## Endpoints and analysis

For policy `p`, arm `a`, design `d` (the paper's Eq. 6–7): `q` = fraction of
draws correct; `μ` = multiplicity-weighted `F` among correct draws; `F = q·μ`.

- **Primary contrast:** each arm minus `fp16` of the same policy.
- **`μ` contrast** uses designs where both arms have at least one correct draw.
- **Intervals:** paired design bootstrap, resampling designs within
  family × regime strata, 10,000 resamples, 95% percentile intervals.
- **Descriptive:** per-design effective number of distinct correct
  implementations (inverse Simpson), and the share of correct draws whose
  structure differs from the policy's FP16 majority form.

## Decision rule

| Outcome | Condition | Action |
|---|---|---|
| A | For some policy, `gptq4` or `gptq3` lowers `μ` with an interval entirely below zero and a point loss of at least 10% of that policy's FP16 `μ` | Proceed to RQ2 |
| A′ | Condition A holds only for RTN arms | Diagnostic only; decide as B |
| B | No GPTQ arm meets A, and every GPTQ point loss in `μ` is below 5% | RQ1 negative; no hidden-cost paper |
| C | `stu_gptq4` correctness below half of `stu_fp16` | Post-training quantization too crude; re-plan with quantization-aware training |
| — | Anything between B and A | Report as inconclusive; extend draws only by a new amendment written before seeing more outcomes |

Trimmed-vocabulary arms are reported with the same contrasts but do not enter
the A/B decision.

## Amendments

1. **2026-10-01, after generation started and before any outcome was
   inspected.**  Family × regime strata in the development split hold only two
   or three designs, which makes stratified bootstrap intervals narrow.  The
   analysis therefore also reports an unstratified paired design-bootstrap
   interval for every contrast, as a descriptive sensitivity check.  The
   decision rule is unchanged and uses the stratified interval.  Fix to the
   launcher (missing `gate0/runs` directory) changed no run setting.
2. **2026-10-03, after generation and before any Vivado result existed.**  All
   three student GPTQ runs (`stu_gptq4`, `stu_gptq3`, `stu_gptq4t`) stopped
   before generating: the float32 Cholesky factorization of one damped Hessian
   (an 8,960-input MLP projection) was not positive definite at 1% damping.
   The factorization now keeps the original computation as its first attempt
   and, only if it fails, retries in float64 with damping 3%, 10%, 30% and
   100% of the mean diagonal, recording every layer that needed it in
   `generation_config.json`.  Runs whose factorization succeeded (all 7B GPTQ
   runs) are therefore unchanged.  The three student runs are rerun from
   scratch with this code; their failed directories are kept.  Correctness
   counts of other arms had been seen when this was written; no frequency
   result had.
