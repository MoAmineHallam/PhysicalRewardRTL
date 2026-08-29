# Preregistration: external RTLLM slice selection

**Frozen:** 2026-08-27, before any model generation or Vivado execution for this slice.

## Question bounded by this package

Can a later, separately preregistered policy comparison be tested on a small external set that is not drawn from the five internal DSP-accelerator families? This package answers only which external tasks are admissible and selected. It does not claim that any policy improves correctness, timing, area, or power on them.

## Universe and balance

The universe is the 50 tasks in official RTLLM 2.0 commit `e67f150603f52d6abf208ed0e97bd77a95b1ee34`. The official top-level categories are Arithmetic, Control, Memory, and Miscellaneous. Exactly two tasks are selected from each category, for eight tasks total.

## Eligibility fixed before selection

A task is eligible only if all of the following are true:

1. The pinned directory contains `design_description.txt`, `testbench.v`, and exactly one `verified*.v`.
2. The description states an identifier-safe module name and the testbench instantiates it.
3. The official reference contains edge-triggered state with exactly one non-reset edge signal.
4. The reference contains no mixed edge/level sensitivity, `initial` block, delay control, real type, system task, or explicit Xilinx primitive.
5. The official oracle terminates, contains success and failure/error markers, has no external file dependency or `break`, and is reproducible. If it uses `$random`, two fresh Icarus processes must return identical codes and byte-identical normalized transcripts.
6. The official reference compiles and produces the official pass marker under Icarus Verilog 12.0 with `-g2012` in both replays.
7. There is no exact identity match in the declared local fine-tuning sources: task name, raw/normalized prompt, or module-name-normalized reference RTL.

These rules use upstream/reference facts and local training provenance only. They do not inspect candidate RTL or physical-design outcomes.

## Deterministic selection

For each eligible task, compute the lowercase hexadecimal SHA-256 of:

```text
external_rtllm_slice_v1|e67f150603f52d6abf208ed0e97bd77a95b1ee34|balanced-two-per-category|<category>|<task_id>
```

Within each category, sort ascending by that digest and then by `task_id`; take the first two. No replacement is permitted after the selection manifest is frozen.

## Frozen exclusions of special note

- `Arithmetic/Divider/radix2_div`: the official reference compiles but its own official testbench reports three failures.
- `Control/Counter/ring_counter`: the official testbench does not elaborate under the frozen Icarus tool and its task name collides with the local RTL library.
- Multi-clock, combinational-only, behavioral-clock-generator, external-data-oracle, and structurally non-synthesizable tasks are excluded by rules that apply uniformly to the 50-task universe.

## Later failure handling

The eight selected task identities are immutable. A later experiment must retain all candidates and use its separately frozen failure penalty for syntax, oracle, synthesis, placement, routing, or timing failure. A failure may not trigger task substitution. Discovery of a protocol bug before model generation requires a versioned amendment and a new slice version; discovery after any candidate outcome is visible must be reported as a limitation, not repaired in place.

## Contamination boundary

The local check covers `dataset.jsonl`, `distill_corpus.jsonl`, `sft_corpus.jsonl`, `sft_corpus_v5.jsonl`, and `rtl_library/**/{spec.txt,design.v}` with their exact hashes recorded in `contamination_report.json`. It does not prove that RTLLM was absent from the base model's public pretraining data because that corpus is unavailable. The paper must say “no detected local fine-tuning contamination,” not “unseen by the model.”

## Prohibited uses before the next preregistration

- Do not generate candidates from these prompts.
- Do not run Vivado or collect timing/PPA for these tasks.
- Do not expose the oracle or upstream reference RTL to the model.
- Do not tune prompts, decoding, reward, or constraints using these eight task outcomes.
