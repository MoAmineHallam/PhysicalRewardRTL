# Research decision: communication placement inside a transformer FFN

**September 27, 2026 — proposed experiments, not demonstrated advantages.**

## Recommendation

Study **where a small amount of communication should occur inside a transformer feed-forward network (FFN)**, then build the accelerator around that restriction. Keep the supervisor's two stages: establish the model–hardware result first; distillation and physical-reward RTL adaptation follow only if it survives.

The central hypothesis is that **a small global signal used before a local nonlinear gate can recover useful cross-channel interactions without requiring dense communication throughout the expanded FFN**. Compare it directly with an equally expensive global signal used after local nonlinear computation. This is a hypothesis about quality per physical communication budget, not a claim that low rank, grouping, or global conditioning is new.

This is the strongest next experiment I recommend given our evidence and resources. It is not yet a defensible claim of a new architecture. Novelty risk is substantial: closely related local/global operators already exist. The contribution would need to be a supported communication-placement principle, a useful whole-FFN restriction and schedule, and a measured improvement beyond strong alternatives. A minor operator variation with an FPGA implementation would not by itself establish the intended paper.

Working research question:

> At a fixed memory, arithmetic and communication budget, does using a compact global message to control local nonlinear computation preserve language quality better than using that message to combine local outputs?

Target workload: small causal language models, batch-one edge inference, explicitly bounded on-chip storage and memory ports. Report prompt processing and growing-context generation separately. Do not change the attention architecture in the initial causal experiment.

## What our evidence actually supports

| Evidence | What it changes in this plan |
|---|---|
| [Completed 24-run screen](SCREENING_RESULTS_20260927.md): dense NLL 6.10890; equal-budget narrow/grouped/shuffled NLL 6.18740/6.25982/6.23907; Monarch 6.26362 versus its dense match 6.16360 | Naive grouping and permutation are insufficient under this recipe. Narrow dense is a required, strong comparator. There is no current architecture win. |
| All three seeds agree on those matched-budget rankings; initialization correction helps grouping but does not reverse the result | Investigate the communication restriction and optimization together. Do not dismiss the result as one unlucky seed. |
| Each run saw 8.39M sampled tokens at context 256, evaluated on reused development data | This is an undertrained screen, not independent evidence about preserved quality, scaling or long context. |
| [Corrected GPU profiling](PROFILE_UPDATE_20260926.md): FFN share changes markedly with attention backend; fixed-shape graph benefits did not translate to faster eager growing-cache generation | Select workloads and include complete requests. GPU attribution cannot establish the FPGA bottleneck. |
| Existing Vivado 2023.1 recognizes and synthesizes both board parts | Tool installation is not blocking. Accelerator implementation, routing and board measurements remain undone. |
| Submitted TCAD work separates correctness gates, physical reward and independent implementation checks | Reuse this experimental discipline. Frequency alone is not the accelerator objective: throughput also depends on cycles, memory and utilization. |

The submitted RTL paper studies the utility of **generated circuits**. Stage 1 studies the hardware executing **the language model**. Those are separate physical objectives. Neither the submitted paper's frequency improvements nor RFT-LM's retrieval scores demonstrate a more efficient transformer.

The present 31.5M model has only about 7.1M FFN parameters; embeddings and other components limit whole-model compression. The 126.7M profiling model has a larger FFN fraction. A claim based on FFN-only savings must show the resulting complete-model benefit at each scale.

## Literature that changes the decision

The original ledger was incomplete in important places. The [updated ledger](RELATED_WORK.md#r33) adds the following precedents; this is a targeted review, not an exhaustive novelty clearance.

- [Building on Efficient Foundations, NeurIPS 2024](https://arxiv.org/abs/2406.16450) already studies structured FFNs, their optimization and self-guided training at substantial LM scales. Our fixed-recipe screen is not a reproduction of its strongest recipe. Include its training approach with its extra compute counted.
- [GroupBERT](https://arxiv.org/abs/2106.05822) retains dense expansion and uses grouped contraction plus output mixing. Our all-projection grouping is not that baseline. An adapted projection pattern is necessary.
- [HDPL, 2026 preprint](https://arxiv.org/abs/2602.07070) combines block-local and low-dimensional global paths and retains dense aggregation projections. It is the closest newly found architectural overlap. We cannot claim invention of a local/global path or of selective projection replacement.
- [Parallel Track Transformers, 2026 preprint](https://arxiv.org/abs/2602.07306) explicitly reduces synchronization through architectural separation. Thus “communication-aware transformer architecture” is already too broad a novelty claim.
- Existing [FABNet](https://arxiv.org/abs/2209.09570), Monarch, fusion and shared-basis work in the ledger require comparison at the layout, buffer and complete-block level. [Masked GLU](https://arxiv.org/abs/2506.23225) also makes gate/value sharing a crowded direction.

**The remaining question is narrower:** whether placement of a bounded collective relative to the FFN nonlinearity gives a better quality/physical frontier when expansion and contraction remain bank-local. The reviewed sources do not establish our particular matched-budget result; that is not proof that no other paper covers it. Check the full operator graph and schedule against these sources and their citations before naming a method or writing a novelty claim.

## A concrete, falsifiable operator family

Use column vectors. Let `x` be the already-normalized FFN input of width `d`. Partition it into `G` channel groups. Let total hidden width be `m`, message width `r`, and omit biases in the first controlled comparison. Each group owns `d/G` input/output and `m/G` hidden channels.

### Communication before the gate: primary hypothesis

\[
z=\sum_{h=1}^{G}P_hx_h,\qquad
a_g=A_gx_g+B_gz,\qquad v_g=U_gx_g,
\]
\[
y_g=D_g\left[\operatorname{SiLU}(a_g)\odot v_g\right].
\]

Here `P_h` has shape `r × d/G`, `B_g` is `m/G × r`, `A_g,U_g` are `m/G × d/G`, and `D_g` is `d/G × m/G`. Concatenate group outputs and retain the ordinary transformer residual connection outside this operator.

The global message influences which local features pass through the gate. Expanded activations and down-projection accumulation stay within their owning group. There is one logical reduction-and-broadcast collective per token per FFN, in addition to unchanged operations elsewhere in the block.

### Communication after local computation: indispensable control

\[
h_g=\operatorname{SiLU}(A_gx_g)\odot U_gx_g,\qquad
z'=\sum_h R_hh_h,\qquad
y_g=D_gh_g+Q_gz'.
\]

`R_h` is `r × m/G`; `Q_g` is `d/G × r`. Both variants have exactly

\[
N_{\mathrm{weights}}=3dm/G+r(d+m)
\]

weights and the same leading multiply-accumulate count per token. Their message dimensions match, but their dependency chains, buffer lifetimes, quantization ranges and physical schedules can differ. Count those differences rather than calling them identical hardware.

A third equal-budget control places `B_g z` in the **value path**, leaving the gate local. This distinguishes a gate-specific effect from the benefit of any global input. Use the same common local tensors at initialization, appropriately scaled global paths, and monitor activation and gradient scales; do not zero both factors of a path and accidentally prevent learning.

### Why this distinction is worth testing

For different groups `g,h`, the floating-point pre-gate cross-group Jacobian is

\[
J_{gh}=D_g\operatorname{diag}\left(v_g\odot\operatorname{SiLU}'(a_g)\right)B_gP_h.
\]

Its rank is at most `r`, but its receiver-side response depends on the receiver's local state. The post-computation variant has `J_gh = Q_g R_h J_local,h`: its cross-group readout uses a fixed `Q_g`.

More specifically, the post-computation output is a sum of functions of separate input groups, so mixed second derivatives between distinct groups vanish. They generally do not vanish in the pre-gate variant. This elementary distinction motivates an experiment; it does not prove better language modeling or a new theorem. It applies to the isolated FFN **after normalization**, not to the whole transformer, where attention and normalization already couple channels.

There is also a disadvantage: with no biases, if `x_g=0`, the pre-gate value path is zero and that output group cannot receive content from another group. The post-computation variant can. Which restriction matters more is empirical.

The pre-gate matrix is algebraically block-diagonal plus a low-rank term. That construction is prior art. The proposed study must survive comparison with HDPL-like paths, ordinary low rank, and global conditioning precedents; changing a name or removing a variational term is not sufficient novelty.

### Concrete sizes, with honest budget matching

For `d=768, m=2048`, an ordinary bias-free SwiGLU has 4,718,592 weights per FFN. With `r=64`, the proposed family uses 2,539,520 for `G=2`, or 1,359,872 for `G=4`. These are **per-FFN counts**, not model compression or speed measurements.

Start at the existing `d=384,m=1024` scale. `G=4,r=36` exactly matches a dense FFN of hidden width 300; `r=72` matches width 344. Hardware-friendly ranks 32 and 64 do not give those exact matches. Use exact arithmetic matches for scientific controls and explicitly count padding or bracket dense widths for physical comparisons. Never silently label a rounded width as equal-budget.

## The hardware hypothesis and its failure modes

Map groups to private SRAM banks and compute clusters. For the pre-gate form:

1. Retain each local input and compute its partial message.
2. Reduce partial messages; broadcast the final message.
3. Stream tiles through local gate/value projections, SiLU and multiplication.
4. Accumulate the local down-projection output without exporting expanded activations.

The post-computation control accumulates `R_h h_h` while processing hidden tiles, then performs its collective and output update. Include local output retention and all synchronization cycles.

An illustrative accounting model starts with partitioned inputs/outputs and a hidden-partitioned dense FFN. Its input all-gather and output reduce-scatter deliver approximately

\[
(G-1)d(b_x+b_{acc})
\]

link-bits per token. A tree reduction/broadcast for the candidate delivers approximately

\[
(G-1)r(b_{acc}+b_z).
\]

These expressions describe a particular topology and dataflow, not a universal lower bound, DRAM traffic, or measured energy. A bus multicast has different wire costs. Reduction precision may exceed message precision. With equal precision assumptions, `r/d=1/12` suggests a 12-fold reduction in this collective's payload, **not a 12-fold accelerator speedup**.

Compare against a well-tiled fused dense FFN, including a single-engine or systolic mapping if that suits the board better. A strong dense design can already avoid spilling the expanded hidden tensor. Weight traffic, scales, packing, bank conflicts, padding, residuals, normalization, attention, KV cache and the vocabulary head all remain in the accounting.

The most serious practical risk is that DDR weight reads dominate. At equal parameter count and precision, a narrow dense FFN may have similar weight traffic and a simpler, well-utilized engine. A small activation collective may be immaterial. Before substantial RTL investment, produce a cycle/byte/bank trace under matched DSP/MAC, SRAM, port and bandwidth limits. Reject the physical hypothesis if realistic dense scheduling removes the headroom.

Primary deployment is PYNQ-ZU; PYNQ-Z2 is a reduced-configuration portability test. The model need not fit completely on chip. State residency and off-chip transfers explicitly. Use Vivado 2023.1 for both. A fast standalone FFN does not establish fast generation if CPU/FPGA boundary transfers dominate; eventually keep block intermediates in the programmable logic or measure every boundary cost.

## Staged execution and decision gates

### A. Freeze the comparison and expose physical limits

Deliver: operator/specification, numerical reference checks, matched resource model, and a short protocol committed **before** results.

- Audit the closest full equations and implementations, especially HDPL and StructuredFFN. Record implementation differences; an FFN-only adaptation is not an end-to-end reproduction of a paper changing attention too.
- Estimate the best dense and candidate schedules at decode and prefill shapes. Include weight streaming and compare at fixed area/storage, not just fixed parameter count.
- Pin a larger corpus, tokenizer, preprocessing and train/dev/test document manifests. [FineWeb-Edu](https://huggingface.co/datasets/HuggingFaceFW/fineweb-edu) is a suitable candidate; create disjoint held-out documents from its train-only release and audit duplicates. The old locally labeled C4 stream lacks sufficient upstream provenance for the main claim.
- Upgrade checkpoint/resume and cost logging before long runs. Keep attention, normalization, tokenizer, context and embeddings identical within each comparison. If modernizing the backbone, run a bridging dense baseline and apply the changes to every arm.

**Gate:** there must be a plausible physical advantage beyond an equally compact dense implementation, and no identified prior work already establishing the same claimed contribution. Otherwise revise or stop before a large sweep.

### B. Bounded mechanism experiment

Start around 32M parameters, context 512, **100M fresh training tokens per arm**. Use two seeds to screen; extend selected candidates to a third seed and 200M tokens if warranted. These remain exploratory budgets, not proof of competitive model quality.

Initial core: full dense, exact-budget narrow dense, grouped-only, pre-gate message, post-computation message, value-path message. Start at `G=4,r=36`; permit one preregistered less restrictive follow-up (`G=2` or a larger message), not an open-ended search for a favorable result. An expanded dense FFN restored only in selected projections can diagnose where quality is lost.

Strong prior-work controls before selecting a winner:

- GroupBERT-style projection pattern adapted to SwiGLU, with actual parameters counted.
- StructuredFFN BlockDense/low-rank with the published self-guided option, plus the existing Monarch control. Temporary dense training paths must vanish at inference, and their training cost is charged.
- HDPL-inspired FFN-only control and, if affordable, a separately labeled faithful configuration. Preserve a fair optimization opportunity rather than handicapping it with our preferred recipe.

Cap recipe search at two predefined optimization recipes per finalist. First report equal-token results; then compare winners under matched training compute. Dense models can spend the same extra compute on additional tokens or tuning. External-teacher distillation remains Stage 2; self-guided training is a Stage 1 optimization control.

Track validation NLL, training stability, gradient scales, parameter/MAC counts and measured training time. Compare message placement at exactly equal budgets. Synthetic cross-group interaction probes can explain a mechanism but cannot replace held-out language quality.

**Gate:** require a repeatable quality–resource frontier improvement over narrow dense and competitive published controls, or a clearly supported route to matched quality with a still-cheaper physical implementation. Beating grouped-only is insufficient. If two bounded settings lose both quality and estimated physical cost after fair training, stop this family.

### C. Confirm quality and build the accelerator

Only survivors proceed to roughly 100–150M parameters and an initial **2.5B-token confirmation budget**, with at least three seeds for the final dense/candidate comparison. Plan context-1024 training for every confirmation arm. Benchmark throughput first; this budget is a planning choice, not a promise of convergence. Include a smaller-scale confirmation to test whether the observation is scale-specific.

Use independent held-out general-text NLL plus a small pinned evaluation suite, such as WikiText-103, LAMBADA, PIQA and HellaSwag. Audit overlap and use tasks where these small models perform meaningfully above floor. Fix evaluation lengths and scoring; test context lengths actually supported by the positional scheme. Report paired seed variation and example uncertainty without treating token correlations or millions of tokens as millions of independent experiments.

Implement matched dense and candidate FFNs, then complete blocks. Validate exported quantized numerics against the model and evaluate the exported model again. Select shared quantization opportunities for both sides; count accumulators and scales. Do not assume 4-bit weights or messages preserve quality because floating-point training passed.

Suggested advance criteria to freeze before confirmation:

- Independent NLL degradation no greater than 0.05 nats/token relative to the chosen full dense quality target (about 5.1% relative perplexity); this is a proposed engineering tolerance, not a universal definition of preserved quality.
- No more than a preregistered 2 percentage-point degradation on each adequately powered downstream task. If uncertainty cannot resolve that margin, report inconclusive preservation rather than passing it.
- At matched acceptable quality, at least 15% complete-block latency reduction **or** 20% energy reduction under fixed area/storage limits, with a useful full-model effect. These are planning thresholds, not predicted results or sufficient conditions for publication.

Freeze one primary hardware endpoint and workload distribution; report all secondary endpoints. Start with batch-one, 512-token prompt plus 128 generated tokens as the primary request; use 128- and 896-token prompts plus 128 generated tokens as shorter/longer controls. These fit within the proposed trained context. Longer-context claims need a separate supported training/evaluation protocol, particularly with learned absolute positions. Measure post-route clock, cycles, utilization, off-chip bytes and total memory. Energy needs a documented measurement boundary and adequate instrumentation; label tool estimates separately. Include prompt-plus-generation latency and growing KV storage, not only a fixed-position replay.

The boards demonstrate FPGA efficacy. A chip claim requires a verified ASIC library/PDK, SRAM model, common constraints and physical flow for both designs. Inventory that route early; if unavailable, write an FPGA-focused claim instead of substituting FPGA frequency for ASIC efficiency.

### D. Distillation and physical-reward adaptation

After Stage 1 succeeds, distill the same teacher into the selected student and the strongest dense student under matched data and compute. Apply RTL SFT, then the submitted paper's correctness-gated physical-reward method. Keep generated-RTL utility and the student's own latency/energy as separate axes.

Use held-out designs, fixed generation/search budgets, failure-aware reporting and an independent implementation check. Include SFT-only and correctness-reward controls. A faster student with worse generated circuits is a trade-off to report, not an automatic win.

Do not add RFT-LM's external memory or supervised router to this core experiment. Its reusable value is the training/evaluation infrastructure and the lessons that retrieval scores can hide degraded language modeling and that a trainable readout matters. Those are methodological assets, not evidence that sparse memory will improve the FFN or chip. Revisit retrieval only for a later workload with an established need.

## Resource allocation and stopping policy

Use the four V100s for independent seeds and controls; avoid distributed training unless a measured need arises. The previous approximately 50–72k tokens/s rates apply to small context-256 configurations only. Benchmark the new model/context/data path before estimating duration. Do not extrapolate the 17.82-minute screen to a 125M, multi-billion-token study.

Planning envelope: about 1–2 weeks for the first model/schedule decision, followed by roughly 6–10 additional weeks for surviving training, RTL, routing and board experiments. This is conditional on implementation effort, data preparation and measured throughput; ASIC access could add substantial time. GPU training and hardware modeling can proceed alongside each other. Boards need power only for connectivity/deployment measurements, not model training or synthesis.

Stop or redirect if the novelty audit finds the same principle already established; if narrow dense dominates after fair recipes; if only an artificial microbenchmark improves; or if the communication savings disappear under realistic weight streaming. Do not try to rescue a failed Stage 1 hypothesis by adding distillation, routing or reinforcement learning until the cause is understood.

Alternative directions are real, but less justified now: attention/KV redesign could matter more on some workloads; state-space/recurrent models change the supervisor's immediate question and need different baselines; RFT memory targets retrieval and adds irregular access; quantization alone is a mature field. Keep these as evidence-triggered pivots, not simultaneous projects.

The useful paper would explain **which interactions require communication, where that communication belongs, and when the resulting hardware wins**. It would include negative cases and an executable matched-quality comparison. Whether that supports a CCF-A submission depends on the novelty and results; our current screen alone does not.

## Deliverables and current state

1. This decision document and the amended reference/search ledger.
2. [Small mathematical probe](analysis/communication_placement_probe.py) and [its output](evidence/research-plan-20260927/communication_placement_probe.json): verifies counts and local derivative properties only; no LM or accelerator result.
3. Next execution deliverables: frozen protocol, stronger baseline implementations, pinned data manifests and a dense/candidate physical cost model, before launching the larger screen.

No new GPU training, board deployment or package installation was started to prepare this proposal. Prior server-idle statements refer to the latest recorded check, not continuous monitoring.
