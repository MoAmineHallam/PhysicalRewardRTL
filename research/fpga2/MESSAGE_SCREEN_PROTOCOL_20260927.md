# Frozen exploratory communication screen

Prepared September 27 and finalized September 28, 2026. This protocol is committed before launching the 100M-token
jobs. Numerical smoke runs use separate output directories and are not quality
evidence or warm-start checkpoints. No settings are selected from their losses.

## Purpose and boundaries

Test communication placement versus exact-budget dense controls, while adding
stronger known projection/training patterns. This is the first bounded mechanism
screen, not the confirmation study or an architectural novelty claim. The HDPL
comparison, near-duplicate/benchmark contamination audit and realistic hardware
schedule remain outstanding before selecting a final research winner.

The analytical ledger shows an important limitation: message and equal-budget
narrow dense FFNs have identical ideal cold-weight bandwidth floors. Any benefit
must survive quality matching and real scheduling. The ledger is not physical
gate approval for a main accelerator or proof of reduced measured DDR traffic.

## Data and model

- FineWeb-Edu revision `87f09149ef4734204d70ed1d046ddc9ca3f2b8f9`,
  `sample/10BT/000_00000.parquet`. Full source SHA256 verified before preparation.
  Source card: <https://huggingface.co/datasets/HuggingFaceFW/fineweb-edu>.
- GPT-2 tokenizer revision `607a30d783dfa663caf39e06633721c8d4cfcd7e`;
  tokenizer file SHA256 `8414cab924d8b9b33013f0d221c5862f365ee9be39c5c2bfae8a5a9e970478a6`.
- 100,663,297 training tokens; 1,048,577 development and 1,048,577 reserved-test
  tokens. Whole documents assigned using normalized-content hashes before
  tokenization. Exactly matching documents cannot cross splits. Final documents
  are token-capped; EOS-concatenated windows can attend across document boundaries.
- This is a reproducible convenience sample from one pinned shard. Near-duplicate
  and benchmark overlap have not been excluded. Reserved test arrays are not
  opened by the trainer and are not used for architecture/recipe selection.
- Decoder: width 384, 6 layers, 6 heads, pre-LayerNorm, causal ordinary attention,
  SwiGLU, tied GPT-2 vocabulary head and learned 4096-entry positional table.
  Training/evaluation context 512; the larger table does not establish extrapolation.

## Arms

All non-FFN tensors use identical name-seeded initialization within each seed.

| Arm | FFN weights at deployment/layer | Purpose |
|---|---:|---|
| dense | 1,179,648 | Full dense quality target |
| dense256 | 294,912 | Equal-budget grouped control |
| dense300 | 345,600 | Equal-budget message control |
| grouped | 294,912 | No message, four groups |
| communication_gate | 345,600 | Message before gate |
| communication_value | 345,600 | Message in value path |
| communication_post | 345,600 | Message after local nonlinear computation |
| groupbert_pattern | 1,032,192 | Dense expansion, grouped contraction, dense output mixing |
| dense896 | 1,032,192 | Equal-budget GroupBERT-pattern control |
| blockdense | 267,264 | Block-diagonal first factor, dense second factor |
| blockdense_guided | 267,264 | Same deployment graph, temporary dense training guidance |
| dense232 | 267,264 | Equal-budget BlockDense control |

The GroupBERT pattern is adapted to SwiGLU, not a full encoder reproduction.
BlockDense uses four factor blocks and rank 96 in fused gate/up and down maps.
Its guided variant adds 1,179,648 training-only weights per FFN, initialized to
the corresponding factor product. A deterministic cosine guide coefficient
decays from one to zero over the first half of training. Evaluation always uses
the deployment graph. The current training implementation still computes the
dense guide at zero coefficient: charge this work, and do not label this an
equal-compute comparison or an optimized reproduction of the published system.

References and relevant code pins are in the [ledger](RELATED_WORK.md#r33).
These implementations derive from equations; no upstream code was vendored.

## Training and evaluation

- Twelve arms, seeds 42 and 43: **24 runs**.
- Each run: 6,144 updates, batch 8, accumulation 4, sequence length 512:
  **100,663,296 next-token targets**. Starting from random weights each time.
- Partition the training stream into context-512 blocks, permute without
  replacement using seed+17000, and consume each block once. Adjacent blocks
  share the boundary input/target token, not a duplicated scored target.
- AdamW LR 0.0003, beta=(0.9,0.95), weight decay 0.1 on all parameters,
  warmup 200 updates and cosine schedule to 10%, gradient clipping at norm 1.
- FP32 parameters/optimizer, CUDA FP16 autocast, dynamic loss scale initially
  1024. A nonfinite loss/gradient or skipped update fails that worker; preserve
  evidence rather than replacing the trial silently.
- Deterministic PyTorch algorithms, cuBLAS workspace `:4096:8`, and the same
  math SDPA backend for all arms. The initial GPU resume diagnostic differed
  before interruption under default kernels, so numerical nondeterminism had to
  be removed before checking exact continuation. Preserve that failed diagnostic.
- Initial and every 1,024 updates: first 131,072 development targets. Final:
  1,048,576 development targets. Fixed nonoverlapping windows; report NLL and
  perplexity. Do not compare short interim evaluations with final scores as if
  the token sets were identical.
- Checkpoint every 256 updates and at controlled pauses/end. State includes
  optimizer, scaler, model, guide buffers, RNG and sampling permutation/cursor.
  Resume refuses changed settings/source/data. New attempt logs retain older
  uncommitted work; aggregate only the accepted checkpoint continuation.
- Record training and deployment parameters separately, training time and source
  hashes. Equal-token comparisons are followed by equal-compute comparisons if
  candidates survive; expensive guidance receives no free compute allowance.

## Assignment and failure handling

Four sequential workers, one per GPU. Both V100a GPUs run seed 42; both V100b GPUs
run seed 43, so each within-seed architecture comparison uses the same GPU type.
Even/odd positions in the arm table divide each seed's work; seed-43 orders reverse
their subsequences. Six runs per worker. No multi-GPU training is used.

Each run has a three-hour timeout; worker stops on failure. No automatic restart
or replacement seed. Data hashes are checked before each run and sampling-chain
hashes must agree within each seed. Cross-worker chain agreement is audited when
results are collected. Parent logs, per-step attempt logs and checkpoints remain
on the shared filesystem; only manifests and aggregate evidence are committed.

## Decision after collection

Compare each structured arm with its exact-budget dense control, and compare
the three message placements directly. Consistent paired directions in both
seeds warrant a third seed/longer follow-up; disagreement is inconclusive.
Beating grouped-only is insufficient. Report all arms and failures.

Do not use the old +0.10 short-pilot rule as proof of preserved quality. Independent
confirmation retains separately frozen quality margins and hardware endpoints.
No distillation, RTL reward, external RFT memory, FPGA deployment or ASIC claim
belongs to this screen. Do not promote a screen winner without resolving the
remaining prior-work and physical comparisons.
