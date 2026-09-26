# Stage 1 execution

September 26 update: corrected profiling and preallocated KV storage are available,
and Monarch/low-rank controls pass algebra, gradient and numerical checks. The
three-seed screening campaign uses the separately frozen
[protocol](../research/fpga2/SCREENING_PROTOCOL_20260926.md). See the
[measurement report](../research/fpga2/PROFILE_UPDATE_20260926.md) and
[current status](../research/fpga2/STAGE1_STATUS.md). The settings below describe
the earlier September 23 pilot unless explicitly updated.

This is a research baseline, not a new architecture or an FPGA accelerator. It
implements a causal decoder with learned absolute positions, pre-LayerNorm,
ordinary multi-head attention, tied token/output embeddings, and a gated SiLU
FFN. Dense gate/up and QKV branches each use a fused projection. No RFT memory,
teacher, distillation, RTL reward, or pretrained checkpoint is used.

## Initial bounded protocol

Frozen before training, 2026-09-23 (UTC/local dates can differ):

| Item | Setting |
|---|---|
| Development workload | General next-token language modeling |
| Pilot graph | Width 384, 6 layers, 6 heads, gated FFN width 1024 |
| Tokenizer | Existing GPT-2 tokenizer, vocabulary 50,257; hash in data manifest |
| Training | From scratch; seed 42; 256 attempted optimizer steps; batch 8, accumulation 4, context 256; 2,097,152 sampled tokens per arm |
| Optimizer | AdamW, peak LR 0.0003, beta=(0.9,0.95), weight decay 0.1 on all parameters; 20-step warmup then cosine to 10%; clip norm 1 |
| Numerics | FP32 parameters/optimizer with CUDA FP16 autocast and dynamic gradient scaling; skipped updates explicitly counted |
| Development evaluation | First 65,536 prepared validation tokens, nonoverlapping context-256 windows; next-token NLL and perplexity |
| Arms | Dense; narrower dense FFN (256); four-group FFN (1024 total hidden); same grouped FFN plus fixed output channel shuffle |
| Pairing | Name-derived shared-parameter initialization and identical sampled-window RNG, verified by sample-order hash |
| Profiling graph | Dense width 768, 12 layers, 12 heads, gated FFN width 2048; random parameters |
| Profiling workload | Batch 1, prompt 512 and 2048, last-token logits only; prefill and one decode step at fixed cache length; 5 warmups and 20 timed calls |

This short pilot checks numerical stability, data handling, training throughput,
and whether the controls learn. It cannot rank finalist architectures or establish
quality preservation. The same token budget is not the same compute budget.
Attention and all non-FFN dimensions remain fixed. Narrow and grouped arms have
equal FFN parameter counts; no quality equivalence is assumed. The shuffle is a
diagnostic known operation, not a proposed novel contribution. The grouped arm
does not reproduce the entire GroupBERT architecture.

The position table supports 4096 positions for profiling. Pilot quality is tested
only at the trained 256-token window. Longer-context quality is not established.

## Data boundary

Reuse the existing locally labeled C4 train/validation JSONL files as a development
source. The original upstream dataset revision and extraction recipe are not yet
verified. The validation source was used by the prior project and is not a fresh
confirmatory test. Public conclusions require a pinned independent evaluation
contract and a broader quality suite.

`prepare_data.py` hashes the original complete files, scans all records, detects
whitespace-normalized exact train/validation document duplicates, and excludes
those documents from training. It also deduplicates training documents. A
near-duplicate or benchmark contamination audit is still required. Source files
are never modified. An explicit flag allows skipping only a malformed final
unterminated record; malformed middle records abort preparation.

Use the first unique records in original file order up to 8,388,608 training and
262,144 development tokens. This is a reproducible convenience sample, not random
sampling of all C4. Tokenize each document independently, append EOS, concatenate,
and cap the final stream. Attention may cross EOS inside a window. Training
samples windows with replacement; validation uses fixed nonoverlapping windows.

No source text, token arrays, checkpoints, credentials, or private host details
are committed. Hashes and aggregated audit counts are recorded as evidence.

## Commands

Run from the repository root in an environment with torch, numpy and tokenizers:

```bash
python -m unittest stage1.test_model stage1.test_data stage1.test_profile stage1.test_structured -v
python -m stage1.prepare_data --train TRAIN.jsonl --validation VAL.jsonl \
  --tokenizer tokenizer.json --out DATA_DIR --allow-truncated-tail
CUDA_VISIBLE_DEVICES=0 python -m stage1.run train --arm dense \
  --data DATA_DIR --out NEW_RUN_DIR
CUDA_VISIBLE_DEVICES=0 python -m stage1.profile_v2 --out NEW_PROFILE_DIR
```

Change `--arm` to `narrow`, `grouped`, `shuffle`, `monarch`,
`monarch_dense_match`, or `lowrank`. For the new screen, use `--init-policy
fan_matched --steps 1024`, with the protocol's paired seeds. Every output directory must
be new; the runner refuses to overwrite results. `final.pt` is a final-model
export, not an exact optimizer/RNG resume checkpoint. These bounded pilots do not
resume after interruption; preserve failures and launch a new run directory.

Record installed versions per run. The first server environment has PyTorch
2.4.1+cu121, tokenizers 0.20.3 and numpy 2.2.6. No dependency installation was
needed. CPU algebra/cache tests also run with PyTorch 2.5.1 locally.

## What the profiler measures

CUDA events measure the eager implementation on the named GPU. Nested profiler
regions identify attention, FFN, and output-head time; do not sum inclusive and
exclusive counters as independent time. SDPA chooses available kernels; inspect
the operator list to determine the actual backend. A cached single query has no
causal mask; a cached multi-token query uses the explicit offset mask, following
the [PyTorch SDPA semantics](https://docs.pytorch.org/docs/main/generated/torch.nn.functional.scaled_dot_product_attention.html).

The v2 profiler compares `torch.cat` with preallocated KV storage and compares
ordinary launches with fixed-shape CUDA graph replay. Graph offsets are captured
constants, so graph results are not growing-context serving latency. Separate
request measurements include prefill plus 32 growing-cache teacher-forced steps.
Use `--decode-backend explicit` to test the mathematically equivalent single-query
attention implementation. The default remains SDPA; explicit is slower for eager
requests in the measured setup despite faster graph replay. Region attribution
uses CPU-event self device work only and excludes duplicate device annotations.

`python -m stage1.ffn_benchmark --out NEW_DIR` checks eager versus Inductor dense
FFNs, including compile time and numerical parity. This isolated-layer comparison
does not establish an optimized full-model baseline. Legacy `stage1.run profile`
is retired; its old raw results remain archived. No GPU result substitutes for FPGA
measurement. Weight and KV byte counts are analytical sizes, not measured DRAM
traffic. Hardware counters, SRAM/bank accounting, and physical implementation
remain outstanding. Random input/weight profiling establishes shapes and timing
only, not language quality. No FPGA power or ASIC claim follows from it.

## Next gates

Hardware toolchain (verified 2026-09-26): use the existing
`C:\Xilinx\Vivado\2023.1\bin\vivado.bat`. The unchanged `toolchain_probe.tcl`
passes synthesis for both board parts in batch mode. A failed `-version` call
was misleading; no reinstallation is needed. See the
[toolchain evidence](../research/fpga2/evidence/toolchain-20260926/inventory.json).

1. Audit the complete data preparation and four pilot runs, including skipped
   updates, matching data/sample hashes, and failure logs.
2. Improve the dense cache/kernel baseline and measure actual movement where
   counters are available. Profile FFN versus attention versus output head.
3. Pin and reproduce a closest structured projection (Monarch/butterfly) and a
   low-rank control. Complete equation/schedule comparison with prior work before
   selecting a proposed mixing restriction.
4. Set a larger training budget from throughput. Use multiple seeds and a pinned
   quality suite; freeze quality margins before confirmatory evaluation.
5. Implement matched dense and structured FPGA schedules under one numerical
   contract, including packing, buffers, bank conflicts and host/DMA costs.

See the [master reference](../MASTER_REFERENCE.md) for the full research gate.
