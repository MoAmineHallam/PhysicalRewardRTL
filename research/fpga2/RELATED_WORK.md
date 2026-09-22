# FPGA2 — Related research and gap ledger

Review date: **2026-09-22**. Companion to the [master reference](../../MASTER_REFERENCE.md).

This is a focused research map, not an exhaustive systematic review. Findings below are attributed to their authors and have not been reproduced here. A reported GPU, FPGA, simulator, or compute-in-memory result is evidence for that setting; it is not an interchangeable ASIC measurement. No headline speedups from different papers are pooled or ranked.

**Read scope:** `A` = primary abstract/metadata reviewed; `T` = relevant full-text sections reviewed; `P` = author-maintained project material also reviewed. An `A` entry is a lead that needs full-method scrutiny before implementing a baseline or asserting a gap. Years identify the linked work's initial release unless a version is stated.

## Structured mathematics: the closest architectural precedents

<a id="r01"></a>
### R01 — FTRANS (2020)

[FTRANS: Energy-Efficient Acceleration of Transformers using FPGA](https://arxiv.org/abs/2007.08563). Scope: A.

**Done:** combines enhanced block-circulant weight representation with an FPGA accelerator for transformer language representations; reports compression and hardware efficiency with limited task degradation.

**Implication:** structured transformer weights plus FPGA acceleration is established. A circulant/FFT block must be a prior-work baseline, not our claimed invention.

**Remaining question for FPGA2:** whether a different communication restriction offers a better quality/physical frontier in small causal decoding under the stated memory limits. The original setting does not automatically answer that question.

<a id="r02"></a>
### R02 — Learned butterfly factorizations (2019)

[Learning Fast Algorithms for Linear Transforms Using Butterfly Factorizations](https://arxiv.org/abs/1903.05895); [primary proceedings paper](https://proceedings.mlr.press/v97/dao19a/dao19a.pdf); [author code](https://github.com/HazyResearch/butterfly). Scope: T/P.

**Done:** learns structured products that represent fast transforms and provides efficient multiplication implementations and compression experiments.

**Implication:** butterfly parameterization and reduced operation counts are established. Multiple sparse stages can still incur communication and scheduling costs.

**Remaining question:** which realizable factor patterns preserve causal LM quality at a fixed physical communication budget. This paper alone does not validate the intended decoder/chip pair.

<a id="r03"></a>
### R03 — Monarch (2022)

[Monarch: Expressive Structured Matrices for Efficient and Accurate Training](https://arxiv.org/abs/2204.00595). Scope: A.

**Done:** uses products of block-diagonal matrices, with the associated structured organization, to obtain expressive efficient transforms; studies approximation, training, and adaptation in vision and language models.

**Implication:** block-diagonal factors with permutations and a language-model quality study are already prior art. Some results involve sparse-to-dense training, so distinguish the final deployed graph from an intermediate training representation.

**Remaining question:** how to restrict and map these factors under our memory/port constraints without losing their quality benefit. A new FPGA port alone would be an implementation contribution.

<a id="r04"></a>
### R04 — FABNet and the adaptable butterfly accelerator (2022 preprint)

[Adaptable Butterfly Accelerator for Attention-based NNs via Hardware and Algorithm Co-design](https://arxiv.org/abs/2209.09570); [full text](https://arxiv.org/html/2209.09570v1); [author code](https://github.com/SamsungLabs/Butterfly_Acc). Scope: T/P.

**Done:** co-designs attention/Fourier and butterfly linear blocks with a reusable FPGA engine. Sections IV–V describe a bank-conflict-aware layout, serial/parallel conversion, shared buffers, and off-chip transfers between some operations. Evaluation includes language/long-range tasks and bandwidth/resource analysis; power is tool-estimated in the reviewed section.

**Implication:** this is a direct predecessor, including memory organization. Do not claim that unified structured engines or bank-aware transformer layouts are missing from prior work.

**Candidate distinction:** a causal autoregressive workload and a separately established advantage from restricting communication across the nonlinear FFN path. Inspect the complete architecture/training regime before asserting a distinction. FPGA-versus-ASIC comparisons reported there do not substitute for our own matched ASIC flow.

<a id="r05"></a>
### R05 — GroupBERT (2021)

[GroupBERT: Enhanced Transformer Architecture with Efficient Grouped Structures](https://arxiv.org/abs/2106.05822). Scope: A.

**Done:** combines attention, convolution, and grouped transformations to reduce dense feed-forward/convolution cost, evaluating BERT-style representations and training efficiency.

**Implication:** grouped FFNs are established. Replacing dense FFNs with groups is a baseline, not sufficient novelty.

**Remaining question:** causal decoding quality and actual digital accelerator communication for a particular constrained grouping/mixing rule. Encoder results must not be treated as decoder results.

<a id="r06"></a>
### R06 — SVD-LLM (2024) and SVD-LLM V2 (2025)

[SVD-LLM](https://arxiv.org/abs/2403.07378); [SVD-LLM V2](https://arxiv.org/abs/2503.12340). Scope: A.

**Done:** the first work addresses truncation error using whitening and parameter updates; V2 allocates heterogeneous compression ratios and improves truncation choices.

**Implication:** low-rank projection and per-matrix rank selection are strong existing compression controls. A compressed factorization adds intermediate tensors and may require two passes through compute/memory.

**Remaining question:** actual quality-matched hardware cost versus our structured family. Verify released versions and distinguish author code from a local reimplementation.

<a id="r07"></a>
### R07 — Basis Sharing (2024 preprint; ICLR 2025 paper)

[Basis Sharing: Cross-Layer Parameter Sharing for Large Language Model Compression](https://arxiv.org/abs/2410.03765); [paper](https://openreview.net/pdf?id=gp32jvUquq). Scope: T.

**Done:** represents weights from different layers with shared bases and distinct coefficients, examining grouping choices and real A100 throughput.

**Implication:** shared bases are not new. Stored parameter reuse does not mean activations from different layers can share one computed projection; layer inputs differ. Hardware benefits depend on retaining/reusing weights and on the schedule.

**Remaining question:** our actual small-batch hardware benefit versus this alternative. Its reviewed throughput setting includes large batches, so transfer to batch-one edge decoding needs measurement.

<a id="r08"></a>
### R08 — SkipCat (2025 preprint; AAAI 2026 paper)

[SkipCat: Rank-Maximized Low-Rank Compression of Large Language Models via Shared Projection and Block Skipping](https://arxiv.org/abs/2512.13494); [full text](https://arxiv.org/html/2512.13494v1); [AAAI paper](https://ojs.aaai.org/index.php/AAAI/article/download/39591/43552). Scope: T.

**Done:** shares a low-rank input projection across matrices receiving the same input, including Q/K/V and gate/up branches. Block skipping further reduces cost; column permutation addresses numerical stability. Appendix G reports A100 prefill, decode, and offloading measurements.

**Implication:** a shared gate/up input basis is directly covered, and the work is not limited to FLOP estimates.

**Remaining question:** whether a different explicit communication constraint provides an advantage beyond a well-mapped version of this method. Any gate/up-sharing proposal must include this comparison.

<a id="r09"></a>
### R09 — LatentLLM (2026 technical-report version)

[LatentLLM: Activation-Aware Transform to Multi-Head Latent Attention](https://merl.com/publications/docs/TR2026-018.pdf). Scope: T.

**Done:** uses activation-aware joint tensor compression, latent attention, and junction-matrix choices that can expose identity subblocks and reduce factorization overhead.

**Implication:** exploiting algebraic freedom in low-rank factors or jointly compressing projections also has close prior art. Algebraically cheap permutations can still have a hardware mapping cost.

**Remaining question:** a physically constrained implementation and quality comparison under our operating regime. Inspect its exact nonlinear boundaries before adapting any transformation.

## Data movement and fusion: mandatory implementation controls

<a id="r10"></a>
### R10 — FlashAttention (2022)

[FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness](https://arxiv.org/abs/2205.14135). Scope: A.

**Done:** exact attention with IO-aware tiling avoids materializing large intermediates in external memory and improves GPU execution.

**Implication:** fewer external transfers can result from a better implementation without changing model mathematics. Dense attention baselines require competent tiling/fusion. A GPU-specific kernel is not automatically usable on V100 or FPGA; validate the selected implementation.

**Remaining question:** additional gains from a changed block after those implementation gains are already accounted for.

<a id="r11"></a>
### R11 — FLAT (ASPLOS 2023)

[FLAT: An Optimized Dataflow for Mitigating Attention Bottlenecks](https://people.csail.mit.edu/suvinay/pubs/2023.flat.asplos.pdf). Scope: T.

**Done:** FusedLogit Attention Tiling fuses dependent attention operations and explores loop ordering/tiling subject to hardware resources for edge/cloud accelerator settings.

**Implication:** SRAM-constrained attention fusion is established. An unfused reference is too weak for a new data-movement claim.

**Remaining question:** the extra benefit from changing the model's structured channel transformations under an otherwise competent dataflow.

<a id="r12"></a>
### R12 — TransFusion (author manuscript labeled MICRO 2025)

[TransFusion: End-to-End Transformer Acceleration via Graph Fusion and Pipelining](https://jnamaral.github.io/CDOL/papers/ZhangMICRO25.pdf). Scope: T.

**Done:** models QKV, attention, normalization, and FFN dependencies with Einsum graphs; DPipe schedules pipelines and TileSeek explores tiling under memory limits, reporting modeled edge/cloud improvements.

**Implication:** whole-layer/stack fusion and memory-limited scheduling are already covered. We cannot claim that prior work only optimizes isolated attention kernels.

**Remaining question:** how a changed mathematical block compares with competent fusion of an unchanged graph. Publication metadata should be checked against the publisher before formal citation; the consulted author PDF contains placeholder DOI fields. This is unrelated to the multimodal image/text paper also called Transfusion.

<a id="r13"></a>
### R13 — GQA (EMNLP 2023)

[GQA: Training Generalized Multi-Query Transformer Models from Multi-Head Checkpoints](https://arxiv.org/abs/2305.13245). Scope: A.

**Done:** uses intermediate numbers of KV heads and uptraining to trade off decoder quality and inference efficiency.

**Implication:** KV-head reduction is an established architectural lever. Keep it fixed in the first FFN comparison; changing it simultaneously would confound attribution.

**Remaining question:** interactions with the selected block can be evaluated later, after the core contribution is isolated.

<a id="r14"></a>
### R14 — DeepSeek-V2 / Multi-head Latent Attention (2024)

[DeepSeek-V2: A Strong, Economical, and Efficient Mixture-of-Experts Language Model](https://arxiv.org/abs/2405.04434). Scope: A.

**Done:** introduces MLA to compress attention state as part of a larger model/system design.

**Implication:** latent KV storage and attention projection restructuring are not new. The complete model also changes other components; its headline system outcomes cannot be attributed solely to MLA in our setting.

**Remaining question:** feasibility and quality at small scale with a concrete memory implementation. This is secondary unless profiling identifies the KV cache as the primary bottleneck.

<a id="r15"></a>
### R15 — Native Sparse Attention (2025)

[Native Sparse Attention: Hardware-Aligned and Natively Trainable Sparse Attention](https://arxiv.org/abs/2502.11089). Scope: A.

**Done:** combines hierarchical compression and selection with hardware-aligned sparse computation, training the sparse attention mechanism natively.

**Implication:** learnable sparsity designed for actual hardware efficiency is established. If sparse memory is introduced, compare complete selection and read costs, not just the selected payload.

**Remaining question:** whether it is relevant to the profiled deployment regime; it is not a mandatory architectural addition to the FFN study.

## Architecture search and co-design

<a id="r16"></a>
### R16 — HAT (ACL 2020)

[HAT: Hardware-Aware Transformers for Efficient Natural Language Processing](https://arxiv.org/abs/2005.14187); [paper](https://aclanthology.org/2020.acl-main.686.pdf); [author code](https://github.com/mit-han-lab/hardware-aware-transformers). Scope: T/P.

**Done:** trains a shared-weight supernet and searches heterogeneous transformer architectures with target-device latency feedback, evaluating translation on different processors.

**Implication:** hardware-aware architecture search is established. Device-specific latency matters, and one architecture need not be best everywhere.

**Remaining question:** a new constrained operator family and its physical implementation, rather than substituting a different search algorithm into the same design space.

<a id="r17"></a>
### R17 — TransCODE (2023)

[TransCODE: Co-design of Transformers and Accelerators for Efficient Training and Inference](https://arxiv.org/abs/2303.14882). Scope: A.

**Done:** jointly explores transformer and accelerator designs using ELECTOR simulation and DynaProp pruning, considering accuracy, latency, energy, and area.

**Implication:** joint model/chip search with multiple physical objectives is already covered. Simulated design-space results and a routed implementation have distinct evidence levels.

**Remaining question:** the specific mathematical restriction and empirically validated benefit of FPGA2, including a matched ASIC flow if chip claims are made.

<a id="r18"></a>
### R18 — Quasar-ViT (2024 preprint)

[Quasar-ViT: Hardware-Oriented Quantization-Aware Architecture Search for Vision Transformers](https://arxiv.org/abs/2407.18175). Scope: A.

**Done:** couples quantization-aware model search with latency/resource modeling and FPGA designs, reporting ImageNet results on ZCU102.

**Implication:** architecture plus precision plus FPGA search is established. Vision classification results do not establish autoregressive language quality.

**Remaining question:** our causal workload and mathematical/communication mechanism. Keep precision matched initially to isolate structure.

<a id="r19"></a>
### R19 — LLMForge (May 2026 preprint)

[LLMForge: Multi-Backend Hardware-Aware Neural Architecture Search with Infinite-Head Attention for Edge Language Models](https://arxiv.org/abs/2605.17653); [full text](https://arxiv.org/html/2605.17653v1). Scope: T.

**Done:** expands per-layer attention choices and combines a model-quality surrogate with evolutionary search and hardware backends. The backends include measured GPU cost and analytical/simulated accelerator cost; small-model training uses matched recipes.

**Implication:** small language-model architecture search, hardware-specific choices, and joint quality/cost optimization are already close prior work. Do not describe all its accelerator results as measured silicon.

**Remaining question:** a communication-constrained operator beyond dimension/head choices, validated at the physical implementation level. Need a direct design-space comparison before asserting novelty.

## Arithmetic and FPGA implementations

<a id="r20"></a>
### R20 — BitNet b1.58 2B4T (2025)

[BitNet b1.58 2B4T Technical Report](https://arxiv.org/abs/2504.12285). Scope: A.

**Done:** releases a natively trained ternary-weight language model and studies its quality and execution efficiency.

**Implication:** ternary representations are established and require appropriate training and kernels. Their training scale cannot be assumed affordable here; fewer weight bits alone do not prove reduced total chip energy.

**Remaining question:** apply precision controls after identifying a structural benefit, then count accumulation, scaling, nonlinearities, and memory cost.

<a id="r21"></a>
### R21 — Scalable MatMul-free Language Modeling (2024; later revisions)

[Scalable MatMul-free Language Modeling](https://arxiv.org/abs/2406.02528); [author implementation](https://github.com/ridgerchu/matmulfreellm); [original author project announcement](https://ncg.ucsc.edu/2024/06/07/new-preprint-scalable-matmul-free-language-modeling-by-ph-d-candidate-ruijie-zhu/). Scope: A/P.

**Done:** studies simplified arithmetic and alternative language-model blocks; the original project includes FPGA hardware, while later versions describe additional deployment settings.

**Implication:** co-designing a lightweight language model around nonstandard arithmetic is established. Pin the paper version before using hardware numbers; do not combine claims from different revisions.

**Remaining question:** our explicitly transformer-based Stage 1 comparison and communication constraint. This is useful context, not a reason to expand Stage 1 into unrelated architectures.

<a id="r22"></a>
### R22 — FlightLLM (2024)

[FlightLLM: Efficient Large Language Model Inference with a Complete Mapping Flow on FPGAs](https://arxiv.org/abs/2401.03868). Scope: A.

**Done:** provides a complete FPGA LLM mapping flow exploiting hardware customization and model compression.

**Implication:** a complete inference pipeline matters, not only a projection microbenchmark. Inspect device and memory assumptions before reusing the design on PYNQ.

**Remaining question:** whether changed mathematics improves over an already competent FPGA mapping. This paper is unrelated to the later flight-safety project sharing the name FlightLLM.

<a id="r23"></a>
### R23 — LUT-LLM (2025 preprint; author repository labeled FCCM 2026)

[LUT-LLM: Efficient Large Language Model Inference with Memory-based Computations on FPGAs](https://arxiv.org/abs/2511.06174); [author code](https://github.com/LUT-FPGA/LUT-LLM). Scope: A/P.

**Done:** co-designs vector-quantized computation, centroid search, and table lookups for FPGA language-model inference, with an AMD V80 implementation.

**Implication:** replacing arithmetic with memory lookups is already a concrete alternative. Table construction, lookup access, and device memory resources must be counted.

**Remaining question:** whether our regular digital operator offers a better frontier in the intended resource regime. A V80 result is not a PYNQ-ZU result.

<a id="r24"></a>
### R24 — ELiTeFormer (July 2026 preprint)

[ELiTeFormer: An Efficient Transformer for FPGAs](https://arxiv.org/abs/2607.03652). Scope: A.

**Done:** combines hybrid linear attention and ternary projections with an FPGA processing-element design, reporting model-quality and VCK5000 deployment results.

**Implication:** linear attention plus ternary FFNs and a custom FPGA engine is not an unoccupied direction. The preprint's author-reported comparisons need workload and quality alignment before use as a baseline.

**Remaining question:** FPGA2's distinct structure and measured trade-off. Do not extrapolate its results to small edge boards or an ASIC.

<a id="r25"></a>
### R25 — HALO (AAAI 2026)

[HALO: Hardware-Aware Quantization with Low Critical-Path-Delay Weights for LLM Acceleration](https://ojs.aaai.org/index.php/AAAI/article/view/39406). Scope: A.

**Done:** incorporates circuit timing and power characteristics into post-training quantization, targeting lower-delay weights and switching activity.

**Implication:** physical-feedback-aware numerical representation is established. The abstract does not alone establish the implementation/evidence details needed for a cross-paper hardware comparison.

**Remaining question:** compare structured mathematics first, then precision under equal quality and implementation conditions; do not label all hardware-informed training as novel.

## Distillation and adaptation: Stage 2 precedents

<a id="r26"></a>
### R26 — MiniLLM (2023 preprint; ICLR 2024 version)

[MiniLLM](https://arxiv.org/abs/2306.08543); [author code](https://github.com/microsoft/LMOps/blob/main/minillm/README.md). Scope: A/P.

**Done:** develops reverse-KL/on-policy distillation for smaller generative language models and evaluates instruction-following behavior. The original title is *Knowledge Distillation of Large Language Models*; the current arXiv page uses *On-Policy Distillation of Large Language Models*.

**Implication:** distillation is an existing training method. Start from a simple matched KD baseline; its use does not establish an architectural contribution. Tokenizer and objective compatibility are prerequisites.

**Remaining question:** whether the selected constrained student recovers useful capability and retains its execution advantage.

<a id="r27"></a>
### R27 — Compact Language Models via Pruning and Knowledge Distillation (2024)

[Compact Language Models via Pruning and Knowledge Distillation](https://arxiv.org/abs/2407.14679); [author project](https://github.com/NVlabs/Minitron). Scope: T/P.

**Done:** investigates depth, width, attention, and MLP pruning with distillation-based recovery to create smaller models from a pretrained parent.

**Implication:** architecture reduction followed by distillation is established. Parent-derived models and newly parameterized structured students have different initialization advantages, so comparisons must disclose them.

**Remaining question:** whether recovery preserves a new structural constraint and its actual hardware benefit, rather than merely reducing parameter count.

<a id="r28"></a>
### R28 — Minitron in practice (2024)

[LLM Pruning and Distillation in Practice: The Minitron Approach](https://arxiv.org/abs/2408.11796). Scope: A.

**Done:** applies pruning/distillation to Llama and Mistral-family models, studies depth versus width pruning, and addresses teacher/data mismatch and subsequent alignment.

**Implication:** the teacher recipe, recovery data, and later alignment influence quality. Both dense and structured students require fair recovery budgets.

**Remaining question:** applying a matched process to our fixed student and measuring what happens after RTL-specific physical-reward training.

## Optional memory research and adjacent architectures

<a id="r29"></a>
### R29 — Memorizing Transformers (2022)

[Memorizing Transformers](https://arxiv.org/abs/2203.08913). Scope: A.

**Done:** augments language models with approximate nearest-neighbor access to a memory of recent key/value pairs, evaluating multiple language domains.

**Implication:** external memory is established. RFT-LM's sparse memory must be positioned against this lineage if revived.

**Decision for FPGA2:** defer the memory operator; retain perplexity checks and clean retrieval/readout ablations as methodological lessons.

<a id="r30"></a>
### R30 — HSA / RAMba (2025)

[Hardware-aligned Hierarchical Sparse Attention for Efficient Long-term Memory Access](https://arxiv.org/abs/2504.16795). Scope: A.

**Done:** uses learned hierarchical chunk selection for long-term access and combines it with Mamba; the arXiv record reports NeurIPS 2025 acceptance. The earlier title referred to random long-context access for Mamba.

**Implication:** hierarchical learned retrieval plus hardware alignment has direct precedents. A memory extension must count selection/search cost and preserve general model quality.

**Decision:** optional later comparison if the target becomes long-context memory access; not a dependency of Stage 1.

<a id="r31"></a>
### R31 — Sparse block-diagonal LLMs on compute-in-memory (2025)

[Efficient In-Memory Acceleration of Sparse Block Diagonal LLMs](https://arxiv.org/abs/2510.11192); [full text](https://arxiv.org/html/2510.11192v1). Scope: T.

**Done:** maps structured sparse/Monarch-style LLM representations to compute-in-memory arrays using customized scheduling and mapping to improve utilization.

**Implication:** structured matrices plus reduced data movement is covered beyond GPUs and FPGAs. This is a close conceptual precedent even though the substrate differs.

**Remaining question:** a conventional digital SRAM/datapath design and a demonstrated change to the model–communication trade-off. Different substrates do not automatically confer novelty.

<a id="r32"></a>
### R32 — Mamba-2 (2024)

[Transformers are SSMs: Generalized Models and Efficient Algorithms Through Structured State Space Duality](https://arxiv.org/abs/2405.21060). Scope: A.

**Done:** develops the structured state-space duality and hardware-efficient algorithms underlying Mamba-2.

**Implication:** alternative recurrent state computation remains a possible future comparison, with different state/memory and quality behavior.

**Decision:** the supervisor selected transformer-block design first. Do not silently change the project into an SSM project because a different asymptotic bound appears attractive.

## What the review supports, and what it does not

The broad objective is feasible as a research direction, but its ingredients are heavily studied. The strongest current candidate is a **specific capacity-versus-communication restriction** with an explicit realizable schedule, studied in a matched small causal decoder and followed through physical implementation and adaptation.

That candidate is an inference from the reviewed evidence. This ledger does not prove that the proposed restriction is absent from all prior work. Before naming a new block, compare its equations and graph against the closest full papers and released implementations. If an existing method expresses the same graph, identify the actual remaining contribution: a new training constraint, a stronger physical schedule, a validated trade-off, or none.

A useful reading order is R04, R03, R05, R08, R12, R19, R31, then the Stage 2 papers. These constrain the proposal most directly. R01 and R09 further limit claims about structured matrices and factorization tricks.
