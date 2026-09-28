# FPGA2 execution checklist

Recorded September 27, 2026. This is the operational checklist agreed with the
user, alongside the detailed [research proposal](RESEARCH_PROPOSAL_20260927.md).
Checked boxes indicate completed deliverables, not research hypotheses proved.

## 1. Define the optimization target — in progress

- [x] Record the initial [workload and comparison contract](WORKLOAD_CONTRACT.md).
- [x] Select PYNQ-ZU as primary hardware and Z2 for a smaller portability check;
  retain the verified Vivado 2023.1 installation.
- [ ] Measure available bandwidth and freeze compute, SRAM, port and numerical
  budgets shared by dense/candidate implementations.
- [ ] Inventory an ASIC flow, technology library and memory models if a custom-chip
  claim is to be made. FPGA results alone are not an ASIC result.

**Exit:** one explicit workload, quality target, resource envelope and primary
physical endpoint. Model configuration may be frozen before measured hardware
limits; mark the latter provisional until verified.

## 2. Implement the controlled model comparison — in progress

- [x] Implement pre-gate, value-path and post-computation message placement in
  the existing causal decoder. Code: [communication.py](../../stage1/communication.py).
- [x] Verify outputs and gradients against independently assembled dense
  matrices; verify shared non-FFN initialization and exact parameter budgets.
- [x] Verify causal/cache behavior, nonzero message gradients, one optimizer
  step and model/config checkpoint reload. All 19 current unit tests pass.
- [x] Document initialization and algebraic counts in the workload contract.
- [x] Implement GroupBERT-pattern and BlockDense/self-guided comparisons with
  exact-budget dense controls; disclose the local SwiGLU adaptations.
- [ ] Complete the HDPL comparison and remaining closest-work checks; inspect
  upstream licenses before any source reuse.
- [ ] Complete exact operator/schedule novelty audit and GPU precision checks.

**Exit:** working, fairly initialized candidates and strong controls. Passing
software tests is not evidence of language quality or hardware benefit.

## 3. Prepare reliable training and evaluation — in progress

- [x] Pin corpus revision, tokenizer and preprocessing; make separate document
  manifests for training, development and independent testing.
- [x] Audit normalized exact duplicates and record hashes/exclusions.
- [ ] Complete near-duplicate and external benchmark overlap checks before
  confirmatory claims. The current corpus is an exploratory single-shard sample.
- [x] Implement optimizer/scaler/RNG resume, sample-order records and periodic
  checkpoints; exact CPU and deterministic GPU continuation pass.
- [x] Freeze arms, seeds, recipes and evaluation rules in the
  [screening protocol](MESSAGE_SCREEN_PROTOCOL_20260927.md) before main jobs.

**Exit:** reproducible data, verified resume and a committed run manifest.

## 4. Screen model quality and hardware feasibility together — in progress

- [x] Launch the frozen 24-trial screen on all four V100s after deterministic
  smoke/resume checks, September 28 at 14:28 Shanghai. Initial updates are healthy.

- [ ] Run approximately 32M-scale models for an initial 100M fresh tokens per
  arm, initially two seeds; expand selected comparisons as specified in the proposal.
- [ ] Build dense/candidate cycle, byte, buffer and bank schedules with equal
  compute/storage limits. Include DDR weight loading, packing and synchronization.
- [ ] Compare equal-token results first; account separately for equal-compute
  recipes and temporary dense guidance costs.

**Exit:** a repeatable or well-supported quality/physical frontier advantage
over smaller dense and strong published controls. Beating grouped-only is not enough.
Stop after the bounded follow-up if dense dominates both quality and physical cost.

## 5. Build and measure the accelerator prototype — pending

- [ ] Implement the surviving FFN and strong dense comparator under one stated
  numerical contract; verify model/export/RTL agreement.
- [ ] Synthesize, place and route; measure resources, clock, cycles and transfers.
- [ ] Deploy to PYNQ-ZU and include host/DMA overhead in the stated boundary.
- [ ] Validate energy instrumentation or clearly label estimated power/energy.

**Exit:** the benefit survives weight streaming and implementation overhead.
Revisit or stop if the analytical communication advantage disappears physically.

## 6. Confirm scale and complete inference — pending

- [ ] Confirm survivors around 100–150M parameters with a proposed 2.5B-token
  budget and three seeds for the final dense/candidate comparison.
- [ ] Evaluate independent language quality, downstream tasks and the exported
  quantized model; include another model scale.
- [ ] Measure complete blocks and prompt-plus-generation requests with growing
  KV storage. Demonstrate a smaller Z2 configuration where feasible.
- [ ] Complete matched ASIC physical evaluation if claiming custom-chip gains.

**Exit:** comparable quality with a meaningful complete-model hardware benefit,
supported by uncertainty estimates and a defensible novelty argument.

## 7. Distill and apply physical-reward adaptation — pending

- [ ] Distill the same teacher into the selected and strongest dense students
  using matched data and compute.
- [ ] Perform RTL SFT, then correctness-gated physical-reward training with the
  submitted paper's controls, fixed search budgets and independent validation.
- [ ] Report student execution cost separately from generated-circuit utility.

**Exit:** downstream usefulness is established without hiding either physical
objective. RFT external memory/router remains outside the core Stage 1 study.

## Execution log

**September 27, first implementation:** steps recorded and linked from the master
reference. Three message-placement FFNs integrated into `Config`/`Decoder`;
19 tests passed locally on CPU (PyTorch 2.5.1), including five new test methods.
The [verification record](evidence/communication-implementation-20260927/validation.json)
includes the command, environment and tested source hashes.
No new GPU campaign, dataset download, FPGA build or board deployment launched.
No training-quality, timing or energy benefit is established.

**Next concrete work:** implement the stronger controls and resumable data/training
path, and construct the matched dense/candidate physical schedule. Boards need
power for access/deployment checks, not for model implementation or synthesis.

**September 28:** stronger controls and resumable training implemented; pinned
data prepared/transferred; 23 CPU tests and 48 GPU FFN precision checks passed.
An initial CUDA continuation diagnostic exposed pre-checkpoint nondeterminism;
the revised deterministic training path passes exact GPU continuation before the main screen.
See the [implementation update](IMPLEMENTATION_UPDATE_20260928.md). Historical
"next work" entries above refer to their recorded milestone, not current completion.

**September 28 launch:** source commit `1bc2bf27c7ddfc591b8531d13b41689102d04d57`
was committed and pushed before launch. Four workers each execute six sequential
jobs. At the initial snapshot, workers had reached steps 156, 156, 112 and 146
of their first 6,144-step runs, with no failure markers. The two seed-42 workers
at equal step 156 have identical sampling chains. Full campaign outcomes remain
pending; do not infer quality rankings from the smoke or initial training losses.
