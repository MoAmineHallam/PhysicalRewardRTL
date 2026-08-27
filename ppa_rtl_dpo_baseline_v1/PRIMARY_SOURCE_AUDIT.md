# PPA-RTL Primary-Source Audit

This package implements an **independent adaptation of PPA-RTL's performance-only best-versus-worst DPO method**. It is not an official reproduction, an authors' implementation, or an evaluation of an authors' checkpoint.

## Sources checked

1. Y. Zhao, W. Fu, S. Li, Y.-X. Hu, X. Guo, and Y. Jin, “Hardware Generation with High Flexibility using Reinforcement Learning Enhanced LLMs,” *62nd ACM/IEEE Design Automation Conference (DAC)*, 2025, IEEE document 11132897. Official author-hosted PDF: <https://ece.k-state.edu/research/hardware-security/papers/DAC2025_RLPFA_Processing.pdf>
2. K-State Hardware Security Lab LLM project page: <https://ece.k-state.edu/research/hardware-security/llm.html>
3. Official released preference tuples, `KSU-HW-SEC/PPA_data` (viewer observed at short commit `37913a5` on 2026-08-27): <https://huggingface.co/datasets/KSU-HW-SEC/PPA_data>

The official project page and dataset were used to audit artifact availability. No complete construction code, DPO training code, raw synthesis reports, or official trained checkpoint was found there as of the audit date.

## What the primary paper establishes

- The method constructs an offline PPA preference dataset from post-synthesis measurements, then applies reference-anchored Direct Preference Optimization (DPO).
- For each functional description, the reference model supplies multiple RTL implementations. The paper filters candidates that cannot be synthesized.
- The experimental construction begins with 3,000 RTLCoder descriptions and evaluates five implementations per description, described as including generated and reference code.
- Synthesis uses Synopsys Design Compiler with a TSMC 90-nm library and extracts power, critical-path delay, and area.
- The three metrics are min-max normalized. The performance-only condition uses weights `(0, 1, 0)`, and the best and worst candidates form one preference pair; groups with no metric difference are omitted.
- The paper reports 1,827 performance-only preference tuples.
- Experiments use DeepSeek-Coder-6.7B and RTLCoder-DeepSeek-6.7B, distinguish RL-only from SFT-then-RL, and report training on eight A100 80-GB GPUs.
- Evaluation is on RTLLM and reports syntax/functional pass@5 plus PPA comparisons.

These points define the method component this package can faithfully adapt: **performance-only post-implementation ranking, best-versus-worst pairing, and DPO from a frozen SFT reference**.

## What is not specified well enough for literal reproduction

The paper does not give all choices needed to rerun the experiment exactly:

- DPO `beta`;
- optimizer, learning rate, batch size, number of epochs or optimizer updates, scheduler, warmup, gradient clipping, numerical precision, or checkpoint schedule;
- full-parameter versus parameter-efficient training details;
- prompt and completion token limits or truncation rules;
- training, prompt-selection, or decoding random seeds, temperature, or top-p;
- whether “five designs including generated and reference code” means five total candidates or five generated candidates plus the reference;
- the scope of min-max normalization and behavior for constant-valued groups;
- a fully specified functional-correctness gate during preference construction;
- how synthesis/evaluation failures enter denominators;
- multi-seed aggregation or seed-selection rules.

The released dataset exposes prompt/chosen/rejected tuples but not the raw PPA records and provenance needed to reconstruct or audit its preferences under this paper's FPGA flow.

## Declared adaptation choices

Every missing choice is frozen in `config.json`. The largest domain changes are explicit:

- same local `sft_v6c_out` start and frozen DPO reference, rather than an official PPA-RTL checkpoint;
- local structured accelerator training split and exact local correctness oracle;
- Vivado 2023.1 on `xc7z020clg400-1`, rather than Design Compiler/TSMC 90 nm;
- a matched budget of 229 EDA attempts and 276 optimizer updates per seed;
- failure-aware 0-MHz accounting;
- two prospective DPO seeds;
- a failure-penalized, equal-sample, true routed timing-closure endpoint on the frozen 20-design evaluation split.

Consequently, any paper table must label this condition **“PPA-RTL performance-only DPO (independent adaptation)”**. A result may support a controlled comparison of reward/training strategies in the local domain; it cannot establish that this implementation matches or beats the official PPA-RTL system on PPA-RTL's original benchmark, model, ASIC library, or compute setup.

## Existing-row decision

`rf_rows.json` contains 229 implemented Fmax labels and no held-out designs, but it is not a valid shortcut to a DPO dataset. The pool mixes known SFT/GRPO candidates with candidates of unknown legacy provenance, does not record per-candidate generation seeds/configurations, and lacks the required prospective two-seed oracle evidence. `existing_rows_audit.json` therefore records `DO_NOT_CONSTRUCT_PREFERENCES_FROM_EXISTING_ROWS`, and `prepare_data.py` will not silently convert those rows into training tuples.
