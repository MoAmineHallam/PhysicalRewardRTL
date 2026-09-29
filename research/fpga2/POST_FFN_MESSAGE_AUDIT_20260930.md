# Post-FFN-message research audit — 2026-09-30

## Decision

Stop the FFN-message family.  The completed matched screen establishes that every
tested message placement and the established structured controls lose to its
matched ordinary dense FFN on held-out language-model loss.  The candidate also
has no demonstrated physical advantage.  It must not proceed to RTL, FPGA, or
Stage 2 distillation.

This is a useful negative result: it prevents an attractive but unsupported
architecture story from consuming further GPU and FPGA time.

## What this audit checked

The objective remains to make a useful model--accelerator pair, not merely to
reduce FLOPs.  For autoregressive inference, a proposal needs to reduce a
measurable transfer or storage cost while retaining a regular dataflow that can
be implemented on the PYNQ-ZU and compared fairly with a dense baseline.

| Direction | Closest prior work found | Decision |
| --- | --- | --- |
| Cross-layer / latent KV cache | [systematic cross-layer KV study](https://arxiv.org/abs/2410.14442), [KVSharer](https://arxiv.org/abs/2410.18517), [FusedKV](https://arxiv.org/abs/2512.03870) | Crowded; do not claim cache sharing as new. |
| Linear or recurrent attention | [GLA](https://arxiv.org/abs/2312.06635), [SpecMamba](https://arxiv.org/abs/2509.19873), [ELiTeFormer](https://arxiv.org/abs/2607.03652) | Crowded and already has FPGA co-design claims. |
| Shared weight dictionaries | [MASA](https://arxiv.org/abs/2508.04581), [ResidualTransformer](https://arxiv.org/abs/2310.02489), [AQLM](https://arxiv.org/abs/2401.06118) | The main mathematical idea is already present. |
| Generic physical-aware search or distillation | [HAT](https://arxiv.org/abs/2005.14187), [LLMForge](https://arxiv.org/abs/2605.17653), [SNAC-Pack](https://lss.fnal.gov/archive/2026/conf/fermilab-conf-26-0339-csaid.pdf) | A new search loop alone is not a research contribution. |
| Grammar-constrained or AST code generation | [type-constrained decoding](https://doi.org/10.1145/3729274), [PATOIS action decoder](https://escholarship.org/content/qt89t646kn/qt89t646kn.pdf), [VeriAssist](https://arxiv.org/abs/2406.00115) | Grammar actions and constrained decoding are established; do not claim their invention. |

This review does **not** prove that no related work exists.  It is a scoped
novelty audit, and any candidate must receive a citation and implementation
comparison immediately before paper claims are made.

## The only candidate worth a bounded feasibility study

### Hardware-resident RTL action interface

Rather than have a student predict one of roughly 50,000 BPE tokens at every
output step, make it predict a typed action in a small RTL intermediate
language:

1. Choose the next legal grammar production from the current parser state.
2. Choose a typed signal, port, or declaration from a bounded symbol table.
3. Copy an identifier from the specification when allowed, or emit a digit in a
   small literal alphabet.
4. Let a deterministic finite-state renderer produce Verilog.

The model therefore learns a factorized distribution

\[
p(a_t \mid a_{<t}, x), \qquad a_t \in A(s_t),
\]

where `s_t` is the grammar/symbol-table state and `A(s_t)` is its legal action
set.  The FPGA keeps `s_t`, the legal-action table, and the renderer on chip.
It reads a small state-specific output matrix rather than a full vocabulary
matrix for every generated action.  This is the potential physical benefit:
the normal decoder's vocabulary projection is a large, irregular weight read;
the proposed action heads and action embeddings are small and regular.

The idea is **not** "grammar constraints save compute."  Ordinary constrained
decoding normally calculates all vocabulary logits and masks illegal ones, so
it does not remove that projection.  It is also **not** a claim that AST action
decoding is new: PATOIS already uses production actions, a small terminal
vocabulary, and copying.  The possible contribution is narrower:

> For RTL generation, can a transformer trained directly on a typed action
> language and co-designed with a hardware-resident grammar/symbol engine
> retain functional RTL quality while eliminating the full-vocabulary decoder
> projection from edge inference?

No paper located in this audit demonstrated that exact model interface together
with a measured FPGA accelerator for RTL generation.  That is a gap to test,
not a novelty claim.

## Why this is stronger than another FFN variant

The previous screen changed a middle-layer matrix while leaving the dominant
external interface unchanged.  This candidate attacks an identifiable physical
object: the decoder vocabulary projection and softmax.  It also gives the
accelerator a deterministic grammar state, bounded action tables, and no
runtime sparse router.  The main risk is quality: action sequences can be
longer than BPE sequences, and identifiers, constants, and semantic constraints
need a carefully designed copy/symbol mechanism.

It is appropriate only for the downstream RTL-generating student; it is not a
replacement for a general-purpose language model.  That specialization is a
feature if the final paper claims an edge RTL-generation system, but it must be
stated plainly.

## Falsifiable first experiment (before a large run)

1. Define a small synthesizable Verilog subset and a canonical action
   serialization.  Record coverage and every unsupported construct.
2. Build two parameter-matched encoder--decoder students: BPE-Verilog and
   action-interface.  Give both identical source specifications, data split,
   teacher supervision, quantization and token/action budget.
3. Report exact model bytes, per-output-step vocabulary-head bytes, action
   sequence length, teacher-distillation loss, parse success, compile success,
   simulation/function pass rate, and held-out PPA of generated circuits.
4. Implement only the output interface and grammar engine first.  Synthesize
   the BPE and action heads under identical clock, precision, memory and I/O
   assumptions on the ZU.  Report post-route resources, cycles, off-chip bytes
   and achieved clock; do not substitute FLOPs for these measurements.

**Advance only if** the action student is competitive on functional RTL quality
and the complete action-interface decode path is materially smaller or faster.
If either condition fails, stop it.  No new large training job should begin
before this feasibility gate passes.

## Role of existing work

The submitted physical-reward method remains useful only after this model-level
gate: distil a selected student, run RTL supervised fine-tuning, then use
correctness-gated physical-reward training with matched dense and action-model
controls.  RFT-LM does not supply this architecture; its reusable lessons are
to retain a normal quality metric beside a task metric, preserve ablations, and
avoid treating a narrow benchmark as proof of a generally good model.
