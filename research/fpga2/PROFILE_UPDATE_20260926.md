# Corrected GPU profiling and structured controls

These measurements refine the baseline; they do not demonstrate a new block,
preserved language quality, an FPGA speedup, or energy savings.

## Corrected measurement contract

Profile the same 126,716,160-parameter random dense decoder at batch 1, FP16,
512/2048 prompt tokens, with last-token logits. Timing runs have no region
annotations. Collect annotations separately, attribute each CPU event's own
device work to its nearest region, and exclude duplicate GPU annotations.
Attributed sums agree with non-annotation device activity sums in these runs.
Fractions describe kernel work, not total request latency.

The new preallocated cache appends only new K/V and attends the valid prefix.
Tests cover causal masks, batch > 1, multi-token continuation, reset, overflow,
and agreement with full-sequence and concatenating-cache calculations. Static
cache storage remains stable; Python validation still has a cost.

Fixed-shape CUDA graph replay isolates launch overhead but captures a fixed
cache position. It is **not** a growing-cache serving implementation. A separate
eager request benchmark evaluates a prompt followed by 32 teacher-forced decode
steps, including output-head evaluation; it excludes tokenization and sampling.

The default SDPA trace uses the Volta CUTLASS memory-efficient attention kernel.
For one cached query only, the `explicit` control computes the same mathematical
scaled dot product, FP32 softmax and value reduction as separate operations.
Prefill retains SDPA. Floating-point operation ordering can differ; CPU and GPU
cache/logit checks pass the documented tolerances.

## Measured results at 2K context

Static cache, full random model, one decode step; milliseconds are medians of
20 timed samples. Methods were measured in fixed order, without a repeated
randomized timing campaign, so small differences are not robust speedup claims.

| GPU / decode implementation | Eager step, ms | Fixed-shape graph, ms | FFN share of attributed kernels | Attention core share |
|---|---:|---:|---:|---:|
| V100a / SDPA | 5.528 | 3.613 | 8.90% | 76.05% |
| V100a / explicit | 6.882 | 1.553 | 26.02% | 31.33% |
| V100b / SDPA | 5.685 | 3.438 | 8.50% | 77.02% |
| V100b / explicit | 6.997 | 1.429 | 25.82% | 31.68% |

The faster fixed-shape device execution does not carry over to the ordinary
Python-driven request. Prompt plus 32 static-cache steps takes **177.68 versus
225.62 ms** on V100a and **182.80 versus 225.64 ms** on V100b, SDPA versus
explicit, using synchronized wall time. More launches and host overhead matter.
Do not call the explicit implementation an end-to-end generation speedup.

With explicit attention, prefill FFNs account for approximately 38% of attributed
kernel time at 2K. This supports continuing a bounded FFN study, while retaining
attention, output head, normalization and host costs in end-to-end accounting.
Even eliminating a 26% kernel component cannot eliminate the remaining 74%.
These proportions are GPU observations, not forecasts of FPGA proportions.

## Dense execution control

An isolated dense FFN on V100b compares eager PyTorch with `torch.compile`,
Inductor, full graph, at width 768 and hidden 2048. Numerical checks pass.
Single-token fixed-shape replay is 0.0583 ms eager versus 0.0707 ms compiled;
512-token replay is 0.1433 versus 0.1219 ms. Ordinary-launch compiled medians
are slower for both tested shapes. Initial compiled calls take 33.76 and 1.24
seconds respectively; compilation is not hidden in the evidence.

This is a warm-weight, isolated-layer diagnostic. It does not establish the best
possible dense kernel or a compiled full-model speedup. A future deployment
comparison must tune both dense and structured implementations equally.

## Traffic evidence boundary

At 2K the FP16 model has 108 MiB FFN weights and 72 MiB valid KV state. These
are logical tensor sizes. A concatenating cache additionally reads and writes
the old KV prefix each step (144 MiB logical copying across all layers); static
storage removes that copying, but not attention's KV reads or new-token writes.
Cache effects mean none of these numbers is a measured DRAM transaction count.

An Nsight Compute 2021.2.2 byte-counter availability probe timed out after 90
seconds without output. Its remaining owned processes were identified and
terminated. No DRAM-counter result was obtained, and the cause is not established.
Do not infer permanent counter unavailability or change driver permissions from
this probe alone. Hardware traffic and power measurements remain outstanding.

## Initialization and established controls

Implemented rectangular Monarch, pinned to the author's
[`fly` revision](https://github.com/HazyResearch/fly/tree/6b73449a6b3e228af9e4afe4f153a384e9b537b9),
and ordinary trainable rank-64 projection factors. Local Monarch outputs match
the author's reference implementations 2 and 3 for expansion, contraction and
padded shapes, within 2.3e-15 in FP64. Independent dense-expansion forward and
gradient tests also pass. These operators are established prior work.

The legacy initialization is a confound. At seed 42, synthetic unit-variance
inputs produce first-FFN RMS 0.01490 dense, 0.00745 narrow, 0.00179 grouped,
and 0.00000395 factorized Monarch. Matching expected projection variance brings
the seven arms to RMS 0.01486–0.01538 in this check. All 42 combinations of
two policies, three seeds and seven arms have finite FP16 outputs/gradients;
relative RMS error versus FP32 stays below the 2% preflight threshold.

This check motivates a disclosed initialization control, not a claim that all
optimization conditions are equal or that legacy initialization explains all
of the earlier quality gap. The new
[screening protocol](SCREENING_PROTOCOL_20260926.md) includes a direct legacy
sensitivity check. No pilot result is promoted to independent confirmation.

## Evidence and reproduction

- [GPU profiles and manifests](evidence/profile-20260926/), with exact source
  snapshots for the SDPA and explicit runs. Earlier snapshots predate structured
  controls; their hashes intentionally differ from later source.
- [Control audit](evidence/controls-20260926/validation.json),
  [dense compiler benchmark](evidence/controls-20260926/dense-compiled.json),
  [author-reference parity](evidence/controls-20260926/monarch-author-parity.json).
- [Author attribution, pinned sources and adaptation boundary](../../stage1/THIRD_PARTY.md).

Use `python -m stage1.profile_v2 --out NEW_DIR --decode-backend sdpa` or
`explicit`, and `python -m stage1.ffn_benchmark --out NEW_DIR`. Legacy
`stage1.run profile` is retired so its ambiguous event export is not reused.
Training remains from scratch; no boards, distillation, RFT memory or physical
reward are involved in these runs.
