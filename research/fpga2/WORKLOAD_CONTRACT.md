# Initial workload and comparison contract

Recorded before new screening on September 27, 2026. Operator definitions and
software checks below are fixed for the first implementation. Hardware limits,
data revisions and the full training recipe remain pending; this is **not** a
ready-to-launch screening protocol. Changes must be versioned before affected runs.

## Scope and endpoints

- Task: causal next-token language modeling, trained from scratch in Stage 1.
- Primary serving request: batch one, 512-token prompt plus 128 generated tokens.
  Secondary requests: prompts of 128 and 896 tokens, each plus 128 generated tokens.
- Primary eventual hardware endpoint: complete-request latency at matched
  acceptable quality and fixed compute/storage limits. Report prefill, decode,
  energy, area and memory separately; do not switch primary endpoint after results.
- Initial screen: width 384, 6 layers, 6 attention heads, total FFN hidden width
  1024; ordinary attention, pre-LayerNorm, learned positions and tied vocabulary
  head remain shared. Retain the existing 4096-entry positional table for the
  bridge comparison, but train/evaluate the initial screen at context 512.
- Confirmation: proposed context-1024 training for all arms. The 896+128 serving
  case is a confirmation workload, not an extrapolation-quality claim about a
  context-512 model. A position table's capacity is not trained-context evidence.
- Quality metrics: NLL/perplexity plus pinned downstream evaluation in confirmation.
  Proposed confirmation margins are +0.05 nats/token and 2 percentage points per
  adequately powered task; freeze statistical decision rules before confirmation.

## Core arms and exact budgets

Bias-free FFNs. `d=384`, `m=1024`, `G=4`, `r=36` for the first message family.
Attention, embeddings, norms and residual connections are identical across arms.

| Arm | Local hidden width, total | FFN weights/layer | Leading MACs/token/layer |
|---|---:|---:|---:|
| Full dense | 1024 | 1,179,648 | 1,179,648 |
| Grouped-only, four groups | 1024 | 294,912 | 294,912 |
| Grouped-budget narrow dense | 256 | 294,912 | 294,912 |
| Message-budget narrow dense | 300 | 345,600 | 345,600 |
| Pre-gate message | 1024 | 345,600 | 345,600 |
| Value-path message | 1024 | 345,600 | 345,600 |
| Post-computation message | 1024 | 345,600 | 345,600 |

Message arms count `3*d*m/G + r*(d+m)` weights. Leading MAC equality excludes
elementwise nonlinearities, additions, reductions and scheduling; include their
costs in hardware evaluation. A narrow dense model executes fewer hidden-channel
nonlinearities than the corresponding message model. Do not call these equal
total runtime or identical hardware workloads.

The implementations are dense PyTorch references to the specified structured
graphs, without routing, external memory, dynamic sparsity or a teacher. They
are not optimized CUDA kernels or evidence of a new operator. Prior-work controls
must be added before interpreting the screen as a competitive research result.

## Initial equations and initialization

See the [proposal](RESEARCH_PROPOSAL_20260927.md) for equations. In software:

- `communication_gate`: global input summary added to the gate preactivation.
- `communication_value`: the same-size global summary added to the value path.
- `communication_post`: summarize local nonlinear hidden states and add their
  global readout to the locally contracted output.

Require `init_policy='fan_matched'`, at least two groups, divisible local widths
and no output shuffle. Message width must be positive and no larger than the
input/hidden dimensions. Both message factors start nonzero.

Local tensors retain the existing `(group, input, output)` layout and name-derived
seeds. Define `a=0.02*sqrt(d)` and
`b=0.02*sqrt(8*d/3)/sqrt(2*layers)` as reference projection gains.

For pre-gate/value variants, initialize local projections with gain `a`, splitting
the selected projection's variance equally between local/global paths. The
message reader uses standard deviation `1/sqrt(d)` across all input groups;
the writer uses `a/sqrt(2*r)`. Local contraction uses gain `b`.

For post-computation, both local input projections use gain `a`. Split output
variance equally between local/global paths. The reader uses `1/sqrt(m)`, the
writer `b/sqrt(2*r)`, and local contraction uses gain `b/sqrt(2)`.

These are expected linear projection second-moment matches, not proof of equal
nonlinear output distributions or gradient scales. The initial activation/gradient
audit and GPU FP16 checks remain prerequisites to the screening protocol. Common
non-FFN tensors are bit-identical for the same seed in the CPU tests.

## Hardware accounting to complete

Use PYNQ-ZU and working Vivado 2023.1. Resource budgets must be common to each
dense/candidate comparison; populate them from a concrete design and measured
board constraints before evaluating speedup. Do not assume all model weights fit
in on-chip memory, or keep only candidate weights warm while streaming dense ones.

Required ledger: MAC/DSP allocation, LUT/FF use, SRAM capacity and ports, reduction
and broadcast topology, accumulator/message precision, buffer lifetime, weight
traffic, activation/KV traffic, scales/padding, stalls and CPU/DMA boundaries.
Compare dense fused/systolic or single-engine mappings, not only a deliberately
communication-heavy dense partition. Whole-block normalization and attention
communication remain even if the FFN uses only one collective.

The link-bit formulas in the proposal are illustrative accounting for one
partition, not measured DRAM traffic or a cycle-accurate performance model.
Data revision, sustained board bandwidth, numerical formats and resource budgets
are explicitly **TBD**. They are not inferred from GPU operator percentages.

## Reproduce current software verification

```bash
python -m unittest stage1.test_model stage1.test_data stage1.test_profile \
  stage1.test_structured stage1.test_communication -v
```

Nineteen tests passed locally. They cover independent dense-matrix output and
gradient comparisons, exact counts, common initialization, finite/nonzero message
gradients, an optimizer update, causal/cache behavior and checkpoint reload.
The optimizer check uses random tokens solely for numerical verification.

Example construction (not a training launch):

```python
from stage1.model import Config, Decoder

model = Decoder(Config(ffn_kind="communication_gate", groups=4, rank=36,
                       init_policy="fan_matched"))
```

The historical `stage1.run` CLI/campaign remains unchanged and does not expose
these arms. Integrate them into the new resumable runner after the data and run
protocol are ready; do not silently append them to the completed old campaign.
