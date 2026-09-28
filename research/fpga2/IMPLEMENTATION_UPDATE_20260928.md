# Stage 1 execution: data, controls and resumable training

Work began September 27 and continued September 28 (Shanghai). Companion to the
[execution checklist](EXECUTION_PLAN.md) and [frozen screen protocol](MESSAGE_SCREEN_PROTOCOL_20260927.md).

## Completed prerequisites

- Prepared and transferred a pinned FineWeb-Edu sample: 100,663,297 training
  tokens, 1,048,577 development and 1,048,577 reserved test tokens. The source
  parquet's full SHA256 matches the upstream object. Tokenizer revision/hash is
  recorded. No dataset package installation was needed.
- Scanned 105,728 source rows; 13 normalized exact duplicates were excluded.
  The included 98,435 documents have no repeated normalized identity across or
  within splits. The [manifest](evidence/message-screen-20260927/data_manifest.json)
  and [document audit](evidence/message-screen-20260927/document_audit.json) are
  committed; text, token arrays and per-document records remain outside Git.
- Added GroupBERT-pattern and BlockDense controls, including deterministic dense
  self-guidance and exact-budget dense comparators. These are equation-based
  SwiGLU adaptations, not complete reproductions of the published systems.
- Added a source/data-pinned trainer with optimizer, loss-scaler, sampling,
  guidance-buffer and RNG checkpoints. Sampling is without replacement over
  fixed context-512 blocks for the first full pass.
- All **23 local tests pass**, including bit-exact CPU continuation, optimizer
  states, exported deployment graphs, sampler epoch boundaries and prior-control
  algebra. The historical pilot runner and old results remain unchanged.
- Both GPU servers were reachable and idle before launches. Outbound internet
  on the servers was unavailable; data was downloaded/prepared on the workstation
  and transferred through SSH. Four short GPU smoke workers exercise all 12 arms.

## GPU checks and a detected reproducibility issue

Both GPU types passed 24 initialization/precision checks each (12 arms × two
seeds), with finite deployment-path gradients. The maximum FP16 relative RMS
error was 0.00083938 (approximately 0.084%). These synthetic FFN checks measure
numerical behavior, not language quality.

The initial CUDA interrupted/full comparison failed: maximum model difference
0.00023446, optimizer difference 0.00000195764. Per-step logs show gradient
differences already at step 1, before the checkpoint boundary, while sample
chains and initial losses matched. This is consistent with nondeterministic
GPU computation, rather than sufficient evidence of missing resume state.

The revised trainer enables deterministic algorithms, fixes the cuBLAS workspace
and uses math SDPA consistently for all arms. Runtime identity now prevents
resume across changed torch version or GPU model. The failed diagnostic remains
on the server under `smoke-0/resume-*`; deterministic rechecks use separate
`smoke-deterministic-*` directories. Main campaign launch requires these checks
to pass. CPU regression tests passed again after this change.

**Deterministic recheck passed:** all 12 full-model smoke runs completed. On the
full-sized guided model, interrupted/uninterrupted model and optimizer states
have maximum absolute difference **0.0**, with identical sampling chains. Four
[smoke summaries](evidence/message-screen-20260927/) retain the measured training
rates and the exact-continuation result. The launcher verifies source hashes
against these completed checks before starting main jobs.

## Hardware accounting and interpretation

The [analytical ledger](evidence/message-screen-20260927/analytical_costs.json)
records weights, leading MACs, nonlinear element counts and illustrative cold
weight/bandwidth floors. Under those assumptions a message FFN and its narrow
dense match have identical weight-loading floors. A quality improvement or a
real schedule advantage is therefore necessary; counting fewer collective bits
alone cannot establish a better accelerator.

Clock, bandwidth and integer precision in that ledger are illustrative inputs,
not measured or quality-validated board settings. No cycle-accurate banking
schedule, routed accelerator, measured power or ASIC evidence has been produced.

## Remaining scope

The 24-trial exploratory screen launched September 28 at **06:28 UTC / 14:28
Shanghai**, after source commit `1bc2bf27c7ddfc591b8531d13b41689102d04d57` was
pushed. Four workers use all four V100s, six sequential jobs each. The launch
snapshot shows steps 156/156/112/146 of the first jobs, all without failures.
Seed-42 workers agree on the sampling-chain hash at equal step 156.
The [launch snapshot](evidence/message-screen-20260927/launch_progress.json)
and four launch receipts preserve worker PIDs, source hashes and commands.

Each run targets 6,144 updates / 100,663,296 scored training tokens, so the
campaign totals 2,415,919,104 token exposures across 24 trials, not that many
unique corpus tokens. Early smoke timings suggest several hours for the queue;
checkpoint/evaluation overhead and sustained throughput determine the actual ETA.

This does not
complete the broader evaluation: HDPL, near-duplicate/benchmark contamination,
equal-compute recipe comparison, third-seed confirmation and realistic hardware
schedules remain outstanding. No reserved-test quality result is used to select
an architecture. No Stage 2 adaptation or RFT memory has been introduced.
