# Plan: a hardware-efficient RTL-generating student — 2026-10-01

**Status:** agreed direction, not a result.  Supersedes the action-interface
candidate in [ACTION_INTERFACE_PAPER_PLAN_20260930.md](ACTION_INTERFACE_PAPER_PLAN_20260930.md)
as the next execution target.  Gate 0 tooling is implemented and tested on CPU
([`student/`](../../student/README.md)); no Gate 0 generation or Vivado run has started.

## 1. Why the target changed

The supervisor's question is unchanged: a model–accelerator pair whose
structure reduces data movement while keeping useful quality, validated on
FPGA.  What changed is where the novelty is expected to come from.

1. **Our own ledger fixes the physics.**  At batch-one decode every token reads
   all decoder weights, the evaluated output-head rows and the KV cache.  An
   FFN restructuring at equal bytes has the same weight-loading floor
   ([analytical costs](evidence/message-screen-20260927/analytical_costs.json)),
   and both FFN screens lost quality at equal bytes.  A new block must therefore
   lower bytes per token at matched quality.
2. **Every established way to lower those bytes is already claimed**, mostly
   with FPGA or chip evidence:

   | Lever | Closest prior work |
   |---|---|
   | Low-bit weights | BitNet b1.58; [TeLLMe](https://arxiv.org/abs/2504.16266); [PD-Swap](https://arxiv.org/abs/2512.11550) (ternary weights resident on an edge FPGA) |
   | Weight reuse across depth | [MobileLLM](https://arxiv.org/abs/2402.14905) (block sharing so weights stay in SRAM); [Relaxed Recursive Transformers](https://arxiv.org/abs/2410.20672); [Mixture-of-Recursions](https://arxiv.org/abs/2507.10524); [Hyperloop Transformers](https://arxiv.org/abs/2604.21254); looped-LM scaling laws ([2604.21106](https://arxiv.org/abs/2604.21106), [2609.01343](https://arxiv.org/abs/2609.01343)) |
   | Smaller KV cache | GQA, MLA, cross-layer KV (see [post-FFN audit](POST_FFN_MESSAGE_AUDIT_20260930.md)) |
   | Smaller output head | [Vocabulary trimming](https://aclanthology.org/2023.findings-emnlp.981/); [syntax-aligned Verilog decoding](https://arxiv.org/abs/2503.14153) |
   | Whole model on chip | Taalas HC1; a [3.16M-parameter INT4 model fully on a KV260](https://www.mikeayles.com/blog/on-chip-llm-kv260/) |

3. **Scale.**  Credible quality evidence for a new general block is now produced
   at 1B+ parameters and 100B+ tokens; four V100s cannot match that.
4. **Fit.**  PYNQ-ZU holds about 2.9 MB on chip (5.1 Mb BRAM + 18 Mb URAM): about
   6M INT4 or 11M ternary parameters, far too small to write useful RTL.  A useful
   student streams weights from the 4 GB PS DDR4 in any design.

Our distinctive asset is different: we can measure the **physical quality of
the circuits a model generates**, with failures counted, and we already have a
physical-reward training method.  The efficient-LLM literature measures
perplexity or pass rates, not generated-circuit PPA.

## 2. Research questions

Two physical axes stay separate throughout (as in the master reference): the
cost of **executing the student**, and the utility of the **circuits it writes**.

- **RQ1 — does compression hurt circuit quality differently from correctness?**
  As a student reads fewer bytes per token (W8/W4/W3 weights, trimmed head,
  smaller dense model; looped variants later), does failure-penalized post-route
  utility `F = q·μ` fall because `q` (correctness) falls, or because `μ`
  (frequency of correct circuits) falls?
- **RQ2 — can physical-reward training recover the loss?**  The submitted paper
  found that RL mostly reweights implementations the SFT policy already emits.
  If compression keeps fast implementations reachable but scrambles their
  probability, correctness-gated physical-reward RL on the compressed student
  should recover `μ`.  Compare against distilling the already-optimized
  7B policy into the student (the existing `student_v1_out` route); for
  reasoning LLMs, DeepSeek-R1 reported distillation beating direct RL on small
  models, so the comparison is open but not assumed.
- **RQ3 — what is the joint frontier?**  Measured PYNQ-ZU decode cost (bytes,
  tokens/s, energy where instrumentation allows) against generated-circuit
  utility, with the selected student implemented end to end.

**Prior-work check (scoped, 2026-10-01).**  Found: RL recovery after compression
for robot policies ([RLRC](https://arxiv.org/abs/2506.17639)), distillation-based
healing of 4-bit LLMs ([2608.20953](https://arxiv.org/abs/2608.20953)), edge-FPGA
TinyLlama ([LlamaF](https://arxiv.org/abs/2409.11424)), many PPA-aware RTL
generators (ChipSeek, RTLSeek, LLM-VeriPPA, COEVO).  Not found: any measurement
of how student compression changes the PPA of generated circuits, or physical-
reward recovery of it.  This is not a novelty clearance; repeat the search before
writing claims.

## 3. Decode-traffic ledger (analytical, `student/footprint.py`)

Logical bytes per generated token, context 1024, FP16 head unless trimmed to
8,192 rows (an assumed size; the real kept count comes from
`make_keep_vocab.py`), 4-bit weights with one FP16 scale per 128 weights:

| Student | FP16 total | W4, full head | W4, trimmed head | W3, trimmed head |
|---|---:|---:|---:|---:|
| Qwen2.5-Coder-0.5B | 1.00 GB (head 27%) | 0.47 GB (head **58%**) | 0.21 GB | 0.17 GB |
| Qwen2.5-Coder-1.5B | 3.12 GB (head 15%) | 1.17 GB (head **40%**) | 0.73 GB | 0.57 GB |
| Qwen2.5-Coder-7B | 14.2 GB | 4.51 GB | 3.48 GB | 2.67 GB |

Consequences: (a) once weights are quantized, an untrimmed head becomes the
largest single read for small students, so trimming and quantization must be
studied jointly; (b) the 7B does not usefully fit beside Linux in 4 GB DDR and
is a teacher only; (c) decode speed on the ZU is bounded by measured PS-DDR
bandwidth divided by these totals, so that bandwidth is measured first.
These are lower bounds, not latency predictions.

## 4. Reused assets (previous project, `moaminehallam/fpga`, branch `claude/amazing-hopper-ytsbvr`)

| Need | Existing code |
|---|---|
| Functional oracle | `oracle.py` (two streams × 1,024 vectors, latency-aligned) |
| Design generators and corpus | `gen_accelerator_catalog.py`, `gen_sft_corpus.py`, `gen_distill_corpus.py` |
| Fresh split | `gen_sealed_split.py` (wrapped by `student/make_dev_split.py`) |
| Frozen generation contract | `eval_sealed.py`, `grpo_oracle.sample_group` (wrapped by `student/eval_compressed.py`) |
| Physical flow | `run_ppa.py`, `ppa_synth.tcl`; V7 setup-period flow; `sweep_catalog.py` board harness |
| SFT / RL | `sft_train_v2.py`, `grpo_train_v5.py`, `train_rf_struct.py`, `canonicalize.py` |
| Checkpoints (to confirm on server) | `sft_qwen_out`, `grpo_qwen` (Qwen-7B); `student_v1_out` (Qwen-1.5B, distilled from `grpo_v8_cont`, 85.9% correct excluding median, median 0%); Study 2 RTLCoder SFT/RF adapters |

## 5. Gate 0 — kill test (about 1–2 weeks, no training)

**Purpose:** decide whether RQ1 is worth a paper before any training or RTL work.

- **Split:** a fresh 20-design development split from `make_dev_split.py`
  (new seed 20261001; sealed and all previously measured designs excluded;
  median extrapolation pool widened to 23/25 before drawing).  The sealed
  split is not touched.  Dev designs are barred from all later training.
- **Policies:** `student_v1_out` (1.5B) and the Qwen-7B SFT/GRPO pair.
  Same tokenizer family, so one kept-vocabulary file serves all.
- **Arms per policy:** FP16; W8, W4, W3 (RTN, group 128, decoder projections,
  head FP16); FP16 + trimmed head; W4 + trimmed head.  The adapter is merged
  before quantization, as deployed.
- **Sampling:** 24 draws per design, temperature 1.0, one generation seed shared
  across arms; frozen oracle; multiplicity retained.
- **Physical:** each distinct correct candidate implemented once with the
  primary flow (Vivado 2023.1, xc7z020, 5.0 ns request) for comparability with
  the paper; identical RTL across arms is implemented once and reused.
- **Measures:** `q`, `μ` (on designs where both arms pass), `F = q·μ`; paired
  design-bootstrap intervals versus FP16 of the same policy.

**Decision rule (freeze in a protocol file before the first draw):**

| Outcome | Reading | Action |
|---|---|---|
| A | At W4 or W3, `μ` falls with an interval below zero and at least 10% relative loss for some policy | RQ1 is real: proceed to RQ2 |
| B | `μ` intervals include zero or loss < 5% at both W4 and W3 for every policy | Compression costs correctness only: RQ1 negative; take RQ3 to the supervisor as a frontier/accelerator paper or stop |
| C | `q` collapses at W4 (below half of FP16) for the 1.5B student | Post-training quantization is too crude; RQ1 needs quantization-aware training first; re-plan |

## 6. Later stages (each gated on the previous one)

1. **Compression ladder (if A).**  Add Qwen2.5-Coder-0.5B (SFT on the existing
   corpus), a GPTQ-style W4 baseline beside RTN, and one looped/shared variant
   only if a converted checkpoint is affordable on V100s.
2. **RQ2 training.**  Correctness-only and RF physical-reward arms on the W4
   student (LoRA on the frozen quantized base, re-quantized after merge and
   re-evaluated), versus distillation from the optimized 7B, two seeds per arm.
   Evaluate on a freshly drawn sealed split with the paper's endpoint.
3. **Accelerator (RQ3).**  Measure PS-DDR bandwidth on the PYNQ-ZU first.  Build
   a weight-streaming W4 decoder with an on-chip KV buffer and trimmed head;
   PYNQ-Z2 remains the board for measuring generated circuits.  Report tokens/s,
   off-chip bytes, resources and timing; energy only with validated instrumentation.
4. **ASIC (optional).**  Only if a chip-level claim is wanted: one pinned
   OpenROAD-class flow for the accelerator core, reported separately.

## 7. Open items for the author

1. Confirm checkpoint paths on the server: `student_v1_out`, `sft_qwen_out`,
   `grpo_qwen`, the Qwen2.5-Coder-1.5B and -7B base directories, and whether
   Qwen2.5-Coder-0.5B is downloaded.
2. Confirm the V100 servers are free and that `env_mas` has transformers/peft
   versions that support `stop_strings` (the frozen sampler needs it).
3. Supervisor agreement on this reframing.
