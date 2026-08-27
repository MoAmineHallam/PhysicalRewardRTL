# PPA-RTL Performance-Only DPO Independent Adaptation — Frozen Protocol

Status: **prepared, not launched**. This directory contains no generated candidates, no new oracle results, no new Vivado labels, no preference dataset, no DPO checkpoint, and no evaluation result.

## Question and allowed claim

The prospective question is whether the repaired RF-reward policy outperforms a published **performance-only best-versus-worst DPO strategy** when both start from the same SFT policy and receive the same local training and evaluation budgets.

The allowed name is **“independent adaptation of PPA-RTL's performance-only best-versus-worst DPO method.”** Because the authors' full implementation and checkpoint are unavailable and the local FPGA domain differs from the paper's ASIC setup, this is not an official or literal PPA-RTL reproduction.

## Matched comparison contract

| Quantity | PPA-RTL DPO adaptation | Repaired-RF condition used for comparison |
|---|---:|---:|
| Initial policy | frozen `sft_v6c_out` | `sft_v6c_out` |
| Eligible training split | same 145 non-held-out, non-CORDIC catalog designs | same declared training domain |
| Functional gate | seeds 1 and 2, 1,024 vectors each | same gate |
| New physical labels | exactly 229 Vivado post-route attempts | 229-label RF budget |
| Failed physical attempt | consumes budget and scores 0 MHz | retained/penalized failure rule |
| Optimizer updates | exactly 276 per seed | 276 |
| Prospective training seeds | 1 and 2 | both RF seeds reported |
| Evaluation | 20 frozen held-out designs, 24 draws/design/seed | same multiplicity |
| Primary physical endpoint | true routed timing closure, all failures 0 MHz | recomputed on the same closure protocol |

The training algorithms are intentionally different: PPA-RTL converts measured candidate rankings into chosen/rejected DPO pairs; the RF condition performs reward-guided policy optimization. “Matched” refers to starting point and budgets, not identical loss functions.

## Phase 0 — mandatory gate

Do not generate candidates or invoke EDA unless `timing_closure_gate_v1/results/pilot_gate.json` is a complete PASS tied to manifest SHA-256 `2e0674f96c57be3864a6fab7683b0edc76f732762f78547d5e6a3e8efc17e194`, with every gate criterion true. A missing, incomplete, mismatched, or failed pilot stops this study.

This gate matters because the local 229-label budget uses the historical 5-ns/WNS proxy for tractable training labels, while the headline evaluation uses true clock closure. The pilot must first show the proxy is sufficiently trustworthy for training-label ordering.

## Phase 1 — prospective candidate construction

`label_plan.json` deterministically freezes 46 prompts sampled only from the 145-design training split, with quotas FIR 8, recursive FIR 8, polynomial 15, IIR 14, and median 1. There are exactly 229 slots:

- one catalog reference candidate for each prompt;
- four new samples from `sft_v6c_out` for 45 prompts;
- three new SFT samples for the frozen four-candidate prompt, `poly10_v4_8b`.

Each generated slot has a frozen sampling seed, temperature 1.0, top-p 1.0, and maximum 1,536 new tokens. A generated slot receives at most 16 declared attempts to produce a candidate passing both oracle seeds. Exhausting that cap makes the construction incomplete; no prompt or label may be substituted.

The catalog reference is included because the PPA-RTL paper describes candidate groups as including generated and reference code. Treating the paper's “five designs” as five candidates total is an explicit adaptation choice, not a recovered author setting.

## Phase 2 — fixed physical-label budget

Only after Phase 0 passes, run one post-route implementation attempt for each of the 229 frozen slots using Vivado 2023.1 and `xc7z020clg400-1` at the declared 5.0-ns request. Every attempt consumes one label slot. Implementation failure, timeout, unconstrained timing, or malformed output receives a failure-aware score of 0 MHz and is not replaced.

For each prompt, record min-max normalized performance for audit but rank by the failure-aware Fmax. Choose the maximum and reject the minimum, resolving score ties deterministically by RTL SHA-256. If all extrema are equal, emit no preference pair and do not add another candidate or EDA attempt.

The prospective label JSONL must contain the exact slot identity/source, generation provenance, both oracle records, EDA-attempt record, complete RTL, RTL SHA-256, and failure-aware Fmax. `prepare_data.py build-preferences` refuses incomplete slot coverage, oracle drift, missing EDA accounting, invalid hashes, or negative/non-finite scores.

## Phase 3 — DPO training

Train two separate seeds, 1 and 2. For each seed:

- initialize the trainable LoRA adapter from `sft_v6c_out`;
- retain a distinct frozen `sft_v6c_out` reference adapter;
- use standard reference-anchored DPO with `beta=0.1`;
- AdamW, learning rate `1e-5`, betas `(0.9, 0.999)`, epsilon `1e-8`, weight decay `0.01`, gradient clipping `1.0`, FP16;
- four preference pairs/eight responses per optimizer update;
- constant schedule, no warmup, exactly 276 optimizer updates;
- seeded reshuffle/cycling over the frozen tuples, reporting repeated exposure;
- checkpoints at updates 138 and 276;
- prompt/completion/sequence maxima 512/1,536/2,048 tokens, failing before training rather than silently truncating a preference.

These hyperparameters are local frozen choices because the primary paper does not report them completely. They must be reported, not attributed to PPA-RTL's authors.

## Phase 4 — held-out true-closure evaluation

Evaluate both update-276 seeds on all 20 frozen held-out designs with 24 independent draws per design and seed. Retain every draw. Score no-module, incorrect, oracle-error, unconstrained, synthesis, implementation, timeout, and closure-search failures as 0 MHz. The primary endpoint is the frozen binary-search routed-closure Fmax, not a single 5-ns WNS extrapolation.

Report each seed separately, between-seed dispersion, and an equal-multiplicity pooled descriptive result. Use paired design-level comparisons to SFT and repaired RF. Never select or headline the better DPO seed.

## Stop rules

Stop without making an efficacy claim if any of the following occurs:

1. timing pilot is not an exact complete PASS for the pinned manifest;
2. any input/config/artifact hash fails validation;
3. fewer or more than 229 frozen physical attempts are recorded;
4. a missing/failed label is replaced or dropped;
5. any generated slot fails the frozen correctness-attempt cap;
6. preference construction lacks exact oracle/RTL/EDA provenance;
7. either training seed fails to reach exactly 276 valid optimizer updates;
8. true-closure evaluation is incomplete or drops multiplicity/failures.

An equal-score prompt can legitimately yield no DPO pair; disclose the number and family distribution. If too few non-tied pairs remain to support training, declare the adaptation infeasible under the matched budget rather than expanding the dataset post hoc.

## Commands that are safe now

These commands only regenerate/audit metadata and run validation/tests:

```text
python -B ppa_rtl_dpo_baseline_v1/prepare_data.py plan --out ppa_rtl_dpo_baseline_v1/label_plan.json
python -B ppa_rtl_dpo_baseline_v1/prepare_data.py audit-existing --out ppa_rtl_dpo_baseline_v1/existing_rows_audit.json
python -B ppa_rtl_dpo_baseline_v1/validate.py
python -B -m unittest ppa_rtl_dpo_baseline_v1.test_package -v
```

There is deliberately no training or EDA launcher in this preparation package. Launch infrastructure should be implemented and separately reviewed only after the timing gate passes and prospective data construction is authorized.

All file and artifact digests in this package are SHA-256 over the exact bytes stored on disk. CRLF/LF normalization or any other text canonicalization is prohibited for provenance hashes.
