# Stage 1: first execution milestone

Updated 2026-09-26. **SSH works on both servers. Corrected profiles and structured
controls are validated; a longer, three-seed development campaign is running.**
No quality preservation, architectural speedup, FPGA accelerator, or ASIC result
is established. The existing Vivado 2023.1 installation passed synthesis smoke
tests for both Z2 and ZU; no new installation or powered board is required for
the current GPU work.

## Current work, September 26

- Completed corrected dense profiling on both GPU types with dynamic/static KV
  storage and SDPA/explicit single-query attention. Attribution totals agree with
  GPU activity totals. Fixed-shape graph and real growing-cache eager request
  measurements are reported separately.
- Compiled dense FFN control passes numerical checks but has shape-dependent
  timing: compilation is not a universal improvement. DRAM-counter probe timed
  out; no measured traffic or energy result is available.
- Implemented pinned rectangular Monarch and trainable low-rank controls, with
  a parameter-matched dense Monarch comparator. Fourteen local tests pass;
  Monarch also agrees with the author's reference functions. GPU precision and
  gradient checks pass all 42 arm/seed/initialization combinations.
- Found a substantial initialization-scale confound and added expected-variance
  matching, while preserving identical shared non-FFN tensors. This is a
  disclosed recipe change, not an architectural contribution.
- Launched seven arms x three seeds at 1,024 updates (8.39M sampled tokens per
  run), plus three seed-42 legacy-initialization checks. Four sequential workers
  use the four available GPUs. The first completed runs have zero skipped
  updates; worker output directories preserve all logs and final checkpoints.
  No result or ranking is inferred before collecting the complete campaign.

Details: [profiling/control report](PROFILE_UPDATE_20260926.md),
[frozen screening protocol](SCREENING_PROTOCOL_20260926.md), and
[campaign launch snapshot](evidence/screening-20260926/launch_snapshot.json).
This status describes a live campaign, not a continuing monitoring service;
recheck worker state before launching additional GPU tasks.

## Earlier milestone, September 23

- Implemented a causal decoder with dense, narrower dense, four-group, and
  grouped-with-output-shuffle gated FFN controls. No distillation or RFT memory.
- Seven local correctness tests passed: grouped algebra and gradients, shared
  initialization/counts, causal masking, single/multiple-token cached decoding,
  context limits, and data corruption/dedup rules. The four model tests also
  passed on the server's PyTorch 2.4.1 environment.
- Audited the existing locally labeled C4 files and GPT-2 tokenizer; prepared
  separate Stage 1 token arrays without modifying source data.
- Completed four matched-token, single-seed training smoke pilots on the two
  V100 servers, plus an eager GPU profile of the 126,716,160-parameter dense graph.
- Inventoried Vivado installations and synthesized a small adder for Z2.

Code and frozen pilot settings: [stage1/README.md](../../stage1/README.md).
Raw evidence: [pilot evidence directory](evidence/stage1-pilot-20260923/).

## Training smoke results

Each arm saw 2,097,152 sampled tokens at context 256 and completed 256 optimizer
updates, with **zero skipped updates**. The sampled-window hash is identical
across all arms. Evaluation scores the same 65,536 development tokens. All models
started from scratch; the common non-FFN tensors were initialized identically.

| FFN control | Parameters | Initial NLL | Final NLL | Final perplexity | GPU |
|---|---:|---:|---:|---:|---|
| Dense | 31,498,368 | 10.92749 | 6.78445 | 884.00 | V100-SXM2 |
| Narrower dense | 26,189,952 | 10.92760 | 6.88930 | 981.72 | V100S-PCIe |
| Four groups | 26,189,952 | 10.93593 | 7.11533 | 1,230.69 | V100-SXM2 |
| Four groups + output shuffle | 26,189,952 | 10.93768 | 7.09273 | 1,203.18 | V100S-PCIe |

These are **pipeline/learning checks**, not competitive language-model results.
The models are severely undertrained. Grouping has not preserved dense quality in
this run; ordinary width reduction is an essential control. Do not infer a
stable architecture ranking from one short seed. The fixed normal initialization
also changes activation variance as fan-in changes; a longer comparison must
check initialization sensitivity rather than attribute all differences to
expressive capacity. GPU type is not balanced across arms, so elapsed training
times are not a fair architecture-speed comparison.

Raw results and per-step metrics are under `training/{dense,narrow,grouped,shuffle}`
in the evidence directory. Manifests identify package versions and exact source
hashes. Checkpoints stay in the isolated remote Stage 1 workspace; they contain
model weights, not an exact optimizer/RNG resume state.

## Data integrity and limitations

The original files contain 214,057 complete training records and 40,599 complete
validation records. One unterminated JSON tail was excluded from each: 1,372 and
1,001 bytes respectively. There were zero whitespace-normalized exact
train/validation overlaps and zero internal training duplicates in that scan.
This does not exclude near-duplicates or benchmark contamination.

Prepared 8,388,608 training tokens from the first 17,395 unique documents and
262,144 development tokens from the first 549 unique documents, including a
possibly partial final document at each token cap. The original source-file,
token-array, and tokenizer hashes are in [data_manifest.json](evidence/stage1-pilot-20260923/data_manifest.json).
Existing file order is used, not random sampling from all C4. The original
upstream revision remains unverified. This reused validation source is a
development set, not an untouched final test set.

## Initial GPU profile

Dense graph: width 768, 12 layers, 12 heads, gated hidden width 2048, FP16 inference,
batch 1. Random weights and token IDs; only last-token logits are computed.
The profile tests execution shapes, not language quality at these context lengths.

| Prompt length | Prefill median CUDA-event time | One cached decode step |
|---:|---:|---:|
| 512 | 5.714 ms | 7.236 ms |
| 2048 | 10.991 ms | 7.210 ms |

Twenty calls follow five warmups. Decode is measured repeatedly at a fixed cache
length, not as a complete generated sequence. This eager implementation uses
dynamic concatenation for K/V, and launch overhead can dominate. The results are
not a tuned deployment reference or a throughput guarantee.

The raw profiler contains duplicate region names from CPU-side annotations and
device-side events. Their inclusive times differ; **do not sum them or use them
to claim an FFN time fraction**. The next profiler revision must record event
device types and distinguish attributed kernel time from elapsed region time.
No FFN-dominance decision is justified by this trace yet.

Analytical FP16 sizes for this graph: FFN weights 108 MiB, attention-projection
weights 54 MiB, tied token/output weights 73.619 MiB, and KV state at 2048 tokens
72 MiB. These are sizes, not measured memory traffic. SRAM/bank transfers,
off-chip byte counters, and power have not been measured.

## Vivado decision

Use **Vivado 2023.1, SW build 3865809**, for initial Stage 1 hardware work and
keep the tool version matched across architecture comparisons. On September 26,
the existing installation launched in batch mode, acquired the synthesis license,
and successfully synthesized the probe for both `xc7z020clg400-1` and
`xczu5eg-sfvc784-1-e`. The process exited 0. Both runs had zero errors and zero
critical warnings; each reported that parallel synthesis criteria were not met.
See the [new inventory](evidence/toolchain-20260926/inventory.json) and
[complete synthesis log](evidence/toolchain-20260926/synthesis.txt).

**Correction:** the earlier 2023.1 version-only command printed `ECHO is off`
and returned 1. That did not establish that batch execution was broken. A direct
batch test now succeeds without changing the installation. The previous wording
that its launcher generally failed was too broad. No repair, reinstallation,
device-database copying, or license modification was needed.

The 2026.1 device query returns no `xczu5eg-sfvc784*` parts. Zynq UltraScale+
MPSoC device support is missing from this installation; the ZU synthesis step
was not run. Attempts to download that package repeatedly failed at AMD's
download-link service. Installing it is no longer required to begin ZU work,
because the existing 2023.1 installation already supports the device. Retain
the working 2026.1 installation; no 2023-versus-2026 PPA comparison was performed.
This is an installation gap, not evidence that the board is unsupported by
Vivado in general. AMD's [installer documentation](https://www.amd.com/en/support/adaptive-socs-and-fpgas/installer-info-general.html)
describes selecting device families.

The adder is an unconstrained in-memory tool/license smoke test, not a PPA or
timing result. No bitstream was loaded onto either board. Board connectivity,
PYNQ image compatibility, and measurement setup remain unverified. The initial
probe log was generated on September 22 by the Windows host; the GPU pilots ran
on September 23 UTC. See [toolchain inventory](evidence/stage1-pilot-20260923/toolchain_inventory.json).

## What must run next

1. Collect all 24 screening results; verify paired sample hashes and successful
   updates, report every seed and the legacy-initialization diagnostic. Compare
   structured arms against both full dense and their equal-parameter dense
   controls before selecting anything for a larger study.
2. Finish the equation/schedule novelty audit against the closest full papers.
   The implemented Monarch, grouping, shuffle and low-rank controls are known
   operators, not proposed new blocks. Define explicit buffer/bank/traffic
   schedules and obtain physical or counter evidence for movement claims.
3. Select a larger pinned corpus and independent, broader evaluation suite;
   establish a matched optimization budget and quality margins before
   confirmatory runs. Current 8M-token development screens are undertrained and
   do not establish competitive language quality or long-context behavior.
4. Use the verified 2023.1 toolchain and verify board access. Define fixed-point arithmetic,
   then implement and compare matched dense/structured FFN schedules with honest
   buffer, bank, DMA and timing accounting. Expand to full-block/model costs.

Stage 2 remains deferred until the Stage 1 quality/physical gate is met.
