# Stage 1: first execution milestone

Updated 2026-09-23. **Four short pilots and one GPU profile completed. No quality
preservation, architectural speedup, FPGA accelerator, or ASIC result is established.**
All four GPUs were idle at the final live check; no continuing experiment was left running.

## Completed

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

Use **Vivado 2026.1, SW build 6511674**, provisionally for all Stage 1 comparisons.
It launches and synthesizes the `xc7z020clg400-1` test successfully. The installed
2023.1 files remain, but its launcher fails both normally and with a cleaned
process environment; no 2023-versus-2026 PPA comparison was performed.

The 2026.1 device query returns no `xczu5eg-sfvc784*` parts. Zynq UltraScale+
MPSoC device support is missing from this installation; the ZU synthesis step
was not run. Add the proper 2026.1 device package and repeat the probe before
implementing ZU hardware. Do not copy device databases from another release.
This is an installation gap, not evidence that the board is unsupported by
Vivado in general. AMD's [installer documentation](https://www.amd.com/en/support/adaptive-socs-and-fpgas/installer-info-general.html)
describes selecting device families.

The adder is an unconstrained in-memory tool/license smoke test, not a PPA or
timing result. No bitstream was loaded onto either board. Board connectivity,
PYNQ image compatibility, and measurement setup remain unverified. The initial
probe log was generated on September 22 by the Windows host; the GPU pilots ran
on September 23 UTC. See [toolchain inventory](evidence/stage1-pilot-20260923/toolchain_inventory.json).

## What must run next

1. Correct profiler event attribution, implement a preallocated KV cache, and
   test tuned dense FFN execution. Repeat same-device profiling and obtain actual
   movement counters or clearly bounded analytical schedules. Decide whether the
   FFN intervention is valuable for the chosen workload.
2. Pin and implement the closest Monarch/butterfly and low-rank controls; finish
   the equation/schedule novelty audit before naming any new block.
3. Check initialization sensitivity, then train longer with at least three
   finalist seeds and a broader pinned evaluation suite. Set the budget from a
   representative longer throughput measurement, including startup/evaluation,
   checkpointing and search costs. Freeze quality margins before confirmation.
4. Add ZU device support and verify board access. Define fixed-point arithmetic,
   then implement and compare matched dense/structured FFN schedules with honest
   buffer, bank, DMA and timing accounting. Expand to full-block/model costs.

Stage 2 remains deferred until the Stage 1 quality/physical gate is met.
