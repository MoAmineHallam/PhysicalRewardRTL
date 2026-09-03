# 1  Source, Objectives, and Significance of the Research Project

## 1.1 Source of the Research Project

This project originates from supervisor-directed research on hardware-friendly large language models (LLMs), FPGA design automation, and the physical evaluation of LLM-generated register-transfer-level (RTL) code. It extends the author's completed research on correctness-gated policy optimization for FPGA accelerator RTL. The completed work established an end-to-end experimental pipeline covering natural-language specifications, supervised fine-tuning (SFT), reinforcement learning, executable functional verification, Vivado synthesis and implementation, and live PYNQ-Z2 measurements. The proposed research retains that verified foundation and adds a focused comparison of dense Transformer, state-space, and hybrid LLM architectures at inference time.

The central idea is that hardware efficiency must be evaluated at two connected levels. The first is the efficiency of the LLM itself while producing RTL, including latency, throughput, memory traffic, energy, and compilation behavior on modern accelerators. The second is the physical utility of the generated RTL after functional verification and FPGA implementation. Existing studies usually examine only one of these levels. This project will build a unified, reproducible framework that measures both.

The proposed work is an independent academic research project undertaken as the author's master's thesis at Harbin Institute of Technology, Shenzhen. It uses existing laboratory computing and FPGA resources. No external commercial deliverable or unverified funding commitment is assumed in the research design.

## 1.2 Objectives and Significance of the Research Project

The overall objective is to determine which LLM architecture and deployment configuration provides the best end-to-end trade-off for FPGA RTL generation when both model inference cost and generated-circuit quality are measured. In this thesis, an architecture is considered hardware-friendly relative to a specified accelerator, precision, software stack, and workload when it improves measured latency, throughput, memory, or energy at a prespecified level of task quality. Hardware-friendliness is therefore an empirical, platform-dependent property rather than a universal label.

The research will address four questions:

- RQ1: On the same GPU and software environment, how do a dense grouped-query-attention Transformer, a pure state-space model, and a hybrid attention-state-space model differ in prefill latency, decoding latency, throughput, peak memory, energy, and arithmetic intensity across context lengths and batch sizes?
- RQ2: After comparable task adaptation, how do these architectures differ in RTL compilation rate, functional pass@1 and pass@k, output length, and robustness on both accelerator-specific and general Verilog tasks?
- RQ3: Under an equal number of generations, which model produces the highest failure-penalized post-route FPGA performance, and what LUT, flip-flop, DSP, BRAM, and estimated-power trade-offs accompany that performance?
- RQ4: Under fixed GPU-time, energy, and EDA budgets, which architecture produces the greatest yield of correct and physically useful RTL?

The work has scientific significance in three respects. First, it replaces vague or theoretical statements about hardware friendliness with measured, accuracy-constrained comparisons. Second, it connects LLM inference research to electronic-design-automation outcomes. A model that generates tokens quickly is not necessarily useful if its RTL fails to compile, is functionally incorrect, or produces a slow circuit. Conversely, a high-quality model may be impractical if its latency and memory footprint prevent adequate sampling. Third, the work introduces a fixed-budget system-level view: the useful output of an RTL-generation system depends jointly on model speed, correctness probability, candidate diversity, verification cost, and physical implementation quality.

The engineering significance is equally direct. LLM-assisted hardware design systems must decide which models to deploy, how many samples to generate, which candidates to verify, and when expensive EDA evaluation is justified. The proposed benchmark and decision framework will provide evidence for these choices on accessible GPU and FPGA platforms. The work will also quantify when the LLM is the bottleneck and when simulation or Vivado dominates the end-to-end workflow.

# 2  Current Research Status and Analysis at Home and Abroad

## 2.1 Research Status at Home and Abroad

The Transformer established attention-based sequence modeling as the dominant language-model architecture [1]. Standard multi-head attention offers strong parallelism during training, but its attention matrix has quadratic prefill complexity in sequence length. During autoregressive generation, a key-value (KV) cache avoids recomputing past states, but the cache grows linearly with context length and every new token attends over an increasingly long history. These properties make memory capacity, memory bandwidth, and data movement central inference constraints.

International research has developed several complementary responses. Multi-query attention shares one set of key and value heads across query heads [2]. Grouped-query attention (GQA) generalizes this idea and was shown to approach multi-head-attention quality while retaining inference benefits [3]. The expected KV-cache ratio relative to conventional multi-head attention is approximately the number of KV heads divided by the number of query heads when the other dimensions are fixed; consequently, a universal percentage reduction should not be assumed. FlashAttention instead preserves exact attention while tiling computation to reduce reads and writes between high-bandwidth memory and on-chip SRAM [4]. PagedAttention and vLLM address serving-level fragmentation and KV-cache management [5].

Research in China has contributed important long-context and sparse-computation architectures. DeepSeek-V2 introduced Multi-head Latent Attention (MLA), which compresses KV representations into a latent space, together with a sparse mixture-of-experts design [6]. Native Sparse Attention combines compressed global context, selective token blocks, and sliding local windows with hardware-aligned kernels [7]. These methods demonstrate that algorithmic complexity alone does not predict realized speed: block size, arithmetic intensity, memory layout, kernel maturity, and batch scheduling determine whether a theoretical reduction becomes a wall-clock gain.

State-space models offer a more fundamental alternative. Mamba uses input-dependent selective state-space updates and hardware-aware scan algorithms to obtain linear sequence processing without an attention KV cache [8]. Mamba-2 develops the state-space-duality formulation and reports a faster core layer while remaining competitive with Transformers in language modeling [9]. Hybrid systems such as Jamba interleave attention, Mamba, and mixture-of-experts blocks to combine precise content-based retrieval with efficient long-sequence processing [10]. Falcon Mamba and Falcon-H1 provide pure and hybrid open-weight model families at practical scales [11], [12]. These results motivate direct measurement, but they do not establish that state-space or hybrid models preserve identical reasoning or code-generation capability on every task.

Sparse mixture-of-experts models activate only a subset of parameters per token and can expand total model capacity without proportional arithmetic cost [13]. However, expert routing, load imbalance, communication, and weight residency can limit performance on a single GPU. Native low-bit approaches such as BitNet b1.58 reduce weight representation cost by training with ternary weights [14], but realized gains depend on native training and specialized kernels. For this reason, the main experiment will focus on three executable architecture classes at a comparable scale. MLA, large MoE systems, sparse attention, and native low-bit models will be treated as related work or optional operator-level studies rather than being combined into an uncontrolled end-to-end comparison.

LLM-based RTL generation has developed in parallel. VerilogEval and RTLLM established executable benchmarks for natural-language-to-Verilog generation [15], [16]. VeriGen, RTLCoder, Qwen2.5-Coder, CraftRTL, and related systems demonstrated the value of domain-specific pretraining, synthetic data, supervised adaptation, and targeted repair [17]-[20]. LoRA makes such specialization practical without changing the underlying base-model weights [21]. Group Relative Policy Optimization (GRPO), introduced in the DeepSeekMath work, supplies a resource-efficient policy-optimization method that has subsequently been applied to executable code and RTL objectives [22].

Recent hardware-design research moves beyond syntax and simulation. VeriSeek applies code-structure-guided reinforcement learning [23]. PPA-RTL and ChipSeek integrate synthesis-derived objectives into LLM training [24], [25]. RTL-OPT supplies a benchmark for RTL optimization with correctness and PPA evaluation [26], while Dr. RTL uses tool-grounded agentic rewriting and critical-path feedback [27]. Pre-synthesis timing and PPA predictors reduce EDA cost [28], but reward-model research warns that optimization can drive a policy away from the data distribution on which a predictor was validated [29]. These findings motivate the proposed separation between a proxy used for training and real executable or post-route measurements used for reporting.

## 2.2 Literature Review and Analysis

### 2.2.1 Hardware-Friendly LLM Architecture and Inference Evaluation

The literature establishes several useful architectural principles but also reveals a methodological problem. Papers often report throughput or memory improvements using different models, training corpora, parameter counts, sequence lengths, precisions, kernels, batch sizes, and GPU generations. A reported speedup is therefore conditional on the complete system configuration. The Roofline model helps explain the result by relating achieved computation to arithmetic intensity and platform memory bandwidth [30], but it does not replace end-to-end latency, memory, and energy measurement.

A rigorous comparison must separate prefill from decoding. Prefill processes the input sequence in parallel and exposes the quadratic attention term. Decoding is usually memory-bandwidth-sensitive at low batch size because weights and cached states must be read for each generated token. GQA and MLA primarily reduce KV-state traffic; FlashAttention changes I/O behavior; state-space layers replace the growing cache with recurrent state; and MoE changes active arithmetic while introducing routing and communication. These mechanisms can dominate under different context lengths and batch sizes.

Accuracy must also be treated as an outcome rather than assumed. Statements such as “100% lossless reasoning” are not meaningful without a baseline, benchmark, non-inferiority margin, and confidence interval. The proposed work will therefore report Pareto frontiers instead of creating a single arbitrary score. An architecture will be considered efficiency-superior only when the associated task-quality result satisfies a predefined non-inferiority condition or when the quality-performance trade-off is stated explicitly.

### 2.2.2 LLM-Based RTL Generation and Physical Evaluation

Most RTL-generation benchmarks use compilation and simulation as their final authority. These checks are indispensable, but they do not measure whether a correct circuit is fast, area-efficient, or practical on an FPGA. Physical optimization studies often report the best candidate found after search. That answers whether the search process can eventually discover a good implementation, but it does not show whether the generator's one-draw distribution improved.

The author's completed work addresses this distinction by preserving sample multiplicity and assigning zero physical performance to incorrect or implementation-failed outputs. Its principal metric can be written as

U = (1/N) sum_i I_functional(i) I_implementation(i) Fmax(i),

where the indicator variables retain failures in the denominator. This metric estimates the physical utility of one generation rather than the quality of a selected survivor. The proposed architecture comparison will preserve this estimator and add fixed-time and fixed-energy views. The resulting analysis will distinguish model quality, sampling throughput, oracle cost, deduplication, and EDA cost.

### 2.2.3 Research Gap and Proposed Positioning

The reviewed literature leaves four gaps. First, there is no common accuracy-constrained comparison of dense Transformer, pure state-space, and hybrid models for RTL generation on the same accelerator. Second, generic language or code accuracy does not reveal downstream FPGA physical quality. Third, fixed-sample evaluation ignores the practical advantage of faster inference, whereas pure tokens-per-second evaluation ignores correctness and physical utility. Fourth, learned physical rewards require evaluation on the optimized distribution rather than only on their supervised training distribution.

This thesis will fill these gaps with a two-level benchmark. At the model level, it will measure inference efficiency and use Roofline evidence to interpret bottlenecks. At the design level, it will apply executable verification and real post-route FPGA evaluation. The principal novelty is the connection between the levels: correct implemented RTL per unit compute and failure-penalized physical utility under fixed draw, time, and energy budgets.

# 3  Main Research Content and Research Plan

## 3.1 Research Content

### 3.1.1 Operational Definition, Models, and Fairness Protocol

Three representative architecture classes will form the primary comparison: a dense GQA code Transformer, represented initially by Qwen2.5-Coder-7B; a pure Mamba-2 code model, represented initially by Codestral Mamba 7B or a reproducibly available equivalent; and a hybrid attention-state-space model, represented initially by Falcon-H1 at a feasible parameter scale. Final checkpoints will be frozen after a feasibility pilot and before the confirmatory benchmark.

The comparison will use the same GPU, precision, prompt set, generation parameters, warm-up procedure, and repetition policy wherever technically possible. FP16 will be the common baseline because it is supported by both the available V100 and L40S platforms. Architecture-native optimized kernels or lower precisions will be evaluated separately as a best-available-implementation condition. This prevents a kernel availability difference from being mistaken for an architectural property while still measuring practical deployment performance.

Pretrained-model comparisons cannot completely isolate architecture because training data and optimization recipes differ. The thesis will therefore describe the full-size experiment as an end-to-end system comparison. If resources permit, a smaller matched controlled experiment will train or adapt compact Transformer, Mamba-2, and hybrid models using the same tokenizer, data, parameter budget, and optimization steps. Causal architectural claims will be limited to this controlled component.

### 3.1.2 Inference Benchmark and Roofline Analysis

The inference harness will measure input processing and autoregressive decoding separately. Initial context lengths will be approximately 512, 2,048, and 8,192 tokens, with 32,768 tokens included only after a memory and runtime feasibility gate. Batch sizes will include latency-oriented and throughput-oriented settings. Long-context RTL workloads will use meaningful design context, such as specifications, interface definitions, verification constraints, and related modules, rather than repeated filler text.

The primary model-side metrics will be time to first token, prefill tokens per second, time per output token, decode tokens per second, peak allocated and reserved GPU memory, maximum feasible batch size, state or KV-cache bytes per request, and total generated tokens. GPU energy and average power will be measured through available telemetry after warm-up. Kernel-level profiling will estimate DRAM traffic, achieved FLOP/s, arithmetic intensity, Tensor Core utilization, occupancy, and major stall reasons. Compiler compatibility will be recorded through graph breaks, captured-graph fraction, kernel count, and operator-fusion coverage rather than a subjective “static graph” label.

The benchmark will report raw measurements and Pareto frontiers. No universal hardware-efficiency score will be used as the primary result. Hardware tile alignment, head dimensions, and intermediate dimensions will be recorded as explanatory variables because favorable dimensions depend on accelerator generation, datatype, and kernel implementation.

### 3.1.3 RTL Functional and Physical Quality Evaluation

Each model will receive comparable parameter-efficient adaptation using an oracle-verified training corpus. The existing five circuit families—FIR, reverse FIR, polynomial, IIR, and median-filter accelerators—will be retained for continuity. A new frozen evaluation split will be generated before final model evaluation because the earlier sealed set has already been opened. Public VerilogEval problems will provide an independent general-RTL control.

Every generated sample will be retained. Extraction failure, compilation failure, functional failure, and implementation failure will remain explicit outcomes. Functional verification will use deterministic directed and randomized vectors under multiple seeds, with latency alignment where permitted by the specification. The primary functional metrics will be compile-plus-verdict rate and unbiased pass@1/pass@k estimates.

Distinct correct candidates will be implemented using Vivado 2026.1 for the Zynq-7020 target. The main physical metrics will be true timing-closure frequency where the validated search protocol is feasible, post-route timing-derived frequency otherwise with explicit labeling, LUTs, flip-flops, DSPs, BRAMs, and vectorless estimated power. A prospectively selected subset will be measured on the PYNQ-Z2 using repeated clock sweeps and a co-resident canary. Board power will not be claimed because the available rail telemetry is too coarse for candidate-level measurement.

### 3.1.4 Fixed-Draw, Fixed-Budget, and Statistical Analysis

The first analysis will use an equal number of draws per model and task. This isolates the distributional quality of the model. The second will use equal GPU time and equal measured GPU energy, allowing a faster architecture to generate more candidates. The third will impose an equal EDA budget, which is necessary because unlimited Vivado evaluation could dominate the system cost and conceal the effect of model inference efficiency.

System-level outputs will include correct RTL per GPU-hour, distinct correct implementations per GPU-hour, correct implementations per joule, and failure-penalized post-route utility per generation. A fixed-budget selection analysis will report the best verified implementation obtained within a declared budget, separately from the one-draw distributional endpoint.

All confirmatory choices—models, prompts, sample counts, context lengths, non-inferiority margin, hardware, precision, random seeds, and stopping rules—will be frozen before final evaluation. Comparisons will use paired task-level estimates and bootstrap confidence intervals. Architecture, context length, batch size, and precision interactions will be analyzed without pooling incompatible conditions. Negative results and infeasible configurations will remain in the artifact record.

## 3.2 Research Plan

The research workflow is summarized below.

Table 1  Proposed research workflow and decision gates

| Stage | Inputs and operations | Main outputs and decision gates |
|---|---|---|
| 1. Evidence and protocol freeze | Consolidate completed work; select three architecture classes; define quality margin and budgets | Versioned protocol, model manifest, new unopened task split |
| 2. Inference pilot | Load each model on L40S; validate prompts, kernels, memory, and repeatability | Go/no-go for models, engines, and maximum context length |
| 3. Full inference benchmark | Prefill/decode sweeps; telemetry; profiler collection; common and native implementations | Latency, throughput, memory, energy, compiler, and Roofline results |
| 4. Comparable RTL adaptation | Oracle-verified corpus; matched LoRA/SFT settings; competence gate | Frozen adapters with sufficient RTL-generation foothold |
| 5. Functional evaluation | New frozen accelerator split and VerilogEval; all samples retained | Compile, pass@k, output-length, and specialization results |
| 6. Physical evaluation | Deduplicate correct RTL; Vivado 2026.1 closure/implementation; selected PYNQ sweeps | Failure-penalized Fmax and PPA results with silicon support |
| 7. Cross-layer analysis | Fixed-draw, time, energy, and EDA budgets; paired uncertainty; Pareto analysis | Architecture recommendations by deployment regime |
| 8. Thesis and artifact | Claim-ledger verification, documentation, thesis writing, defense preparation | Reproducible thesis, code, data manifest, paper submission |

The dependency order is intentional. No large evaluation will begin until model loading, generation, oracle correctness, telemetry, and repeatability gates pass. No physical claim will use a learned reward as evidence. Learned proxies may guide training or selection, but executable verification and real EDA measurements remain the reporting authorities.

# 4  Expected Objectives

## 4.1 Expected Objectives

The project is expected to achieve the following objectives:

- Establish a reproducible benchmark for dense GQA Transformer, pure state-space, and hybrid attention-state-space inference on an accessible modern GPU.
- Quantify how prefill, decoding, context length, batch size, precision, cache or recurrent state, and kernel implementation affect latency, throughput, memory, energy, and arithmetic intensity.
- Adapt representative models to RTL generation using a common oracle-verified methodology and measure accuracy rather than assuming lossless capability.
- Extend the existing correctness-gated FPGA evaluation pipeline to a new frozen split and retain all functional and implementation failures in the primary denominator.
- Determine the Pareto-optimal architecture or configuration under fixed-draw, fixed-time, fixed-energy, and fixed-EDA budgets.
- Explain whether faster LLM inference translates into more correct and physically useful RTL, or whether functional verification and EDA become the dominant bottlenecks.
- Produce a versioned research artifact containing prompts, model identities, environment manifests, raw measurements, analysis scripts, and claim-to-artifact provenance.
- Complete a master's thesis and prepare at least one research manuscript based on the verified findings.

Success does not require one architecture to win every metric. A scientifically valuable outcome may be a regime map showing, for example, that one model is preferable for short low-latency prompts, another for long-context generation, and another for quality-constrained FPGA design. Any accuracy, area, energy, or generalization cost will be reported as part of the result.

# 5  Completed Research Work and Schedule

## 5.1 Completed Research Work

The author has completed the core infrastructure and a substantial body of preliminary research. A deterministic functional oracle was developed to evaluate arbitrary I/O-equivalent RTL under directed and randomized stimulus. Oracle-verified corpora were constructed for multiple accelerator implementation styles, and LoRA-based SFT raised the target-domain competence of two independent 7-billion-parameter code models. Five retained circuit families cover feed-forward multiply-accumulate structures, feedback filters, polynomial arithmetic, and comparator-based median filters.

A correctness-gated policy-optimization pipeline was implemented in which only functionally admissible RTL receives a learned physical reward. The workflow includes candidate generation, multiplicity-preserving manifests, Icarus Verilog verification, Vivado synthesis and routing, resource extraction, reward-model diagnostics, and board-side clock sweeping. The work also developed fail-closed preregistration, hash freezing, candidate provenance, claim ledgers, and independent result verification.

In a separately frozen 20-design Study 2, the repaired random-forest reward raised the failure-penalized equal-sample timing-derived endpoint from 35.38 MHz for SFT to 93.01 MHz for the combined RF policies. The paired gain was 57.64 MHz with a frozen 95% stratified-bootstrap interval from 37.69 to 77.20 MHz. Both RF training seeds were positive, and gains appeared in both interpolation and extrapolation regimes. Combined RF correctness was 53.85% compared with 56.25% for SFT, so the primary endpoint already charges the observed functional loss.

Matched controls strengthen the causal interpretation. The RF endpoint exceeded the original MLP-reward endpoint by 26.87 MHz with a paired interval excluding zero. A correctness-only policy raised correctness to 67.40% but reduced failure-penalized Fmax below SFT, demonstrating that the physical-quality gain cannot be explained by generic policy updates or by producing more correct outputs alone.

Conditional PPA analysis showed a real trade-off rather than a free improvement: the RF policy used more LUTs and registers, fewer DSP blocks, and slightly higher Vivado vectorless power on common compiled-correct support. A separate amended descriptive PYNQ-Z2 study produced two large FIR-family wins, two ties, and one median-filter loss. The mean paired silicon difference was positive, but the heterogeneous five-pair result is not treated as universal or independently confirmatory.

An earlier 30-design five-family evaluation and a Qwen2.5-Coder replication support breadth. Historical reward-trajectory analysis also identified a formatting-sensitive reward channel: early optimization produced genuine frequency gains, whereas late optimization raised the proxy without raising measured physical performance. Canonicalization-aware structural features and a bounded random-forest reward were then validated prospectively on the reward-eligible training path.

After repeated host failures with Vivado 2023.1, a supported Vivado 2026.1 installation passed a 40-run infrastructure campaign. The subsequent ten-candidate true timing-closure pilot completed all candidates, achieved a proxy-to-closure Spearman correlation of 0.963, a median symmetric absolute percentage error of approximately 3.5%, no paired sign reversal, and a positive RF-minus-SFT direction. This strengthens the timing interpretation without retrospectively relabeling historical measurements.

A matched 156-problem VerilogEvalV2 control has also been completed. SFT obtained 22.34% pass@1, while the two repaired-RF seeds obtained 21.12% and 20.77%. The seed-averaged difference was -1.39 percentage points. This result will be reported as a small additional general-RTL cost and motivates the accuracy-constrained design of the proposed architecture benchmark.

The current paper draft, “Correctness-Gated Policy Optimization for FPGA Accelerator RTL: A Controlled Post-Route Study,” has been compiled in IEEE TCAD format. It is a manuscript in preparation, not an accepted publication. Remaining actions include supervisor review, final authorship and disclosure decisions, artifact publication, and integration of the newest validated extensions.

## 5.2 Research Schedule

The following schedule assumes proposal approval in September 2026 and a defense around June 2027. It will be aligned with the official university calendar after confirmation.

Table 2  Proposed research schedule

| Period | Planned work | Deliverable |
|---|---|---|
| September 2026 | Finalize proposal; consolidate the current paper; integrate timing-closure and VerilogEval controls; freeze benchmark definitions | Approved proposal and current-work evidence package |
| October 2026 | Select representative models; build common inference harness; perform L40S feasibility and repeatability pilot | Pilot report and frozen model/environment manifest |
| November 2026 | Run prefill/decode, batch, context-length, memory, energy, compiler, and Roofline experiments | Complete model-side inference dataset |
| December 2026 | Construct common adaptation corpus; run matched LoRA/SFT; perform competence and contamination checks | Frozen architecture-specific adapters |
| January 2027 | Generate and freeze a new accelerator evaluation split; run full functional evaluation and VerilogEval control | Accuracy, pass@k, output-length, and specialization results |
| February-March 2027 | Execute Vivado 2026.1 physical evaluation; collect true-closure subset and conditional PPA metrics | Physical-quality dataset and verified analysis |
| March 2027 | Run prospectively selected PYNQ-Z2 confirmation and, if available, one cross-device experiment | Silicon evidence and external-validity assessment |
| April 2027 | Complete fixed-budget and Pareto analyses; robustness checks; draft results and discussion chapters | Frozen tables, figures, and claim ledger |
| May 2027 | Complete thesis writing, internal review, formatting, citation audit, and artifact documentation | Full thesis draft and reproducibility package |
| June 2027 | Incorporate supervisor and committee feedback; prepare slides and oral defense | Final thesis and defense presentation |

# 6  Existing Research Conditions and Funding Assurance

## 6.1 Laboratory Conditions and Funding Assurance

The project already has most of the required hardware and software conditions. Available compute resources include servers with two 32 GB NVIDIA V100-class GPUs and authorized access to NVIDIA L40S GPUs. The existing model workflow supports FP16 training and inference, LoRA adaptation, checkpointed GRPO, and deterministic multi-sample evaluation. The L40S platform is suitable for the primary inference benchmark, while the V100 systems provide a secondary portability point where the required kernels are supported.

The local FPGA environment contains AMD Vivado 2026.1 and a validated flow targeting the Xilinx Zynq-7020 device. The PYNQ-Z2 board supports programmable fabric-clock sweeps, deterministic capture, and repeated functional comparison. Icarus Verilog provides fast pre-screening, and the existing oracle supports deterministic multi-seed stimulus. Repository infrastructure includes frozen manifests, hash verification, structured result files, automated analysis, Word/LaTeX manuscript assets, and Git-based version control.

The research design does not depend on purchasing an H100 GPU, commercial API access, or a new FPGA. Existing institutional and personal research resources are sufficient for the primary plan. Any cloud/API expenditure, second-board experiment, or additional storage will be treated as an optional extension and will require supervisor approval. No specific external grant is claimed in this proposal unless the supervisor or school supplies the corresponding official project information.

## 6.2 Required Conditions and Funding

The remaining required conditions are stable scheduling access to at least one L40S-class GPU, storage for model weights and profiler traces, continued access to the licensed Vivado installation, and periodic access to the PYNQ-Z2 board. A second FPGA family would strengthen external validity but is not required for the principal thesis questions.

Expected direct financial cost is limited because the main hardware, software licenses, and model infrastructure already exist. Potential minor costs include data storage, replacement cables or storage media, and optional API calls for contextual baselines. If long-context or model-size limits exceed available hardware, the study will reduce batch size, use smaller matched models, or limit the maximum context length according to a predeclared feasibility gate rather than requesting uncontrolled additional resources.

# 7  Anticipated Difficulties and Solutions

## 7.1 Anticipated Difficulties and Technical Challenges

The first challenge is fairness across pretrained architectures. Models of similar parameter count may use different tokenizers, training corpora, context lengths, and instruction tuning, so an observed quality difference cannot automatically be attributed to architecture. The second challenge is unequal software maturity. Dense Transformer kernels are highly optimized, whereas Mamba or hybrid kernels may require particular CUDA, PyTorch, or inference-engine versions. A benchmark can therefore measure the library as much as the mathematical architecture.

The third challenge is the tension between efficiency and quality. Faster generation may be accompanied by lower RTL correctness, longer outputs, or weaker generalization. The fourth challenge is long-context validity: repeating short prompts to reach 32K tokens produces a misleading benchmark. The fifth challenge is cost. Full synthesis and timing closure are much slower than model inference, and evaluating every candidate without staging can become infeasible.

The sixth challenge is proxy reliability. The completed work has already shown that a learned reward can exploit formatting or leave its supervised support. The seventh challenge is specialization: domain SFT substantially improved accelerator RTL but reduced performance on general Verilog problems, and the newest RF policies show a small additional pass@1 cost. Finally, FPGA results may depend on tool version, device, seed, constraints, and board harness. One device and one small board sample cannot establish universal silicon behavior.

## 7.2 Solutions

The fairness problem will be addressed by separating end-to-end system comparison from causal architecture claims. Full-size models will be reported with complete model and training provenance. A compact matched experiment will be added if feasible. Model selection will be frozen before confirmatory testing, and results will not be pooled across incompatible parameter scales or software stacks.

Software maturity will be measured explicitly. Every model will have a common-framework FP16 condition and, separately, a native optimized condition. Environment versions, kernel availability, compilation failures, graph breaks, and fallbacks will be preserved. Warm-up, GPU clock state, repetitions, and synchronization will be standardized.

Quality will be protected by a predefined non-inferiority analysis and transparent Pareto reporting. No architecture will be called lossless without direct statistical evidence. The current executable oracle, multiple seeds, public VerilogEval control, and a new unopened accelerator split will prevent speed-only conclusions. Replay data or lower-intensity adaptation will be considered if the pilot shows unacceptable specialization, but any mitigation will be fixed before the final evaluation.

Long-context prompts will be constructed from meaningful hardware-project context. A feasibility gate will determine whether 32K evaluation is possible and relevant. The physical flow will use progressive filtering: extraction checks, compilation, simulation, functional verification, content deduplication, then Vivado implementation. Fixed EDA budgets will be reported separately from fixed generation budgets.

Learned rewards will never serve as final physical evidence. Canonicalization, mutation tests, reward-resolution logging, off-policy error checks, and midpoint/end trajectories will be retained. Final frequency and PPA statements will come from Vivado or bounded live-board measurements. If a proxy is exploited, that negative result will be reported and the affected arm will not be silently repaired after the outcome is known.

Reproducibility will be protected through prospective protocols, multiple seeds where affordable, frozen hashes, explicit failure rows, paired task-level analysis, claim ledgers, and preservation of stopped experiments. Cross-device validation will be attempted only under a separate frozen protocol. Where it is unavailable, the one-device limitation will be stated directly.

# References

[1] A. Vaswani et al., “Attention Is All You Need,” in Advances in Neural Information Processing Systems, 2017.

[2] N. Shazeer, “Fast Transformer Decoding: One Write-Head Is All You Need,” arXiv:1911.02150, 2019.

[3] J. Ainslie, J. Lee-Thorp, M. de Jong, Y. Zemlyanskiy, F. Lebron, and S. Sanghai, “GQA: Training Generalized Multi-Query Transformer Models from Multi-Head Checkpoints,” in Proceedings of EMNLP, 2023.

[4] T. Dao, D. Y. Fu, S. Ermon, A. Rudra, and C. Re, “FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness,” in Advances in Neural Information Processing Systems, 2022.

[5] W. Kwon, Z. Li, S. Zhuang, Y. Sheng, L. Zheng, C. H. Yu, J. E. Gonzalez, H. Zhang, and I. Stoica, “Efficient Memory Management for Large Language Model Serving with PagedAttention,” in Proceedings of SOSP, 2023.

[6] DeepSeek-AI et al., “DeepSeek-V2: A Strong, Economical, and Efficient Mixture-of-Experts Language Model,” arXiv:2405.04434, 2024.

[7] J. Yuan et al., “Native Sparse Attention: Hardware-Aligned and Natively Trainable Sparse Attention,” arXiv:2502.11089, 2025.

[8] A. Gu and T. Dao, “Mamba: Linear-Time Sequence Modeling with Selective State Spaces,” in Conference on Language Modeling, 2024.

[9] T. Dao and A. Gu, “Transformers Are SSMs: Generalized Models and Efficient Algorithms Through Structured State Space Duality,” arXiv:2405.21060, 2024.

[10] O. Lieber et al., “Jamba: A Hybrid Transformer-Mamba Language Model,” arXiv:2403.19887, 2024.

[11] J. Zuo et al., “Falcon Mamba: The First Competitive Attention-Free 7B Language Model,” arXiv:2410.05355, 2024.

[12] J. Zuo et al., “Falcon-H1: A Family of Hybrid-Head Language Models Redefining Efficiency and Performance,” arXiv:2507.22448, 2025.

[13] W. Fedus, B. Zoph, and N. Shazeer, “Switch Transformers: Scaling to Trillion Parameter Models with Simple and Efficient Sparsity,” Journal of Machine Learning Research, vol. 23, 2022.

[14] S. Ma et al., “The Era of 1-bit LLMs: All Large Language Models Are in 1.58 Bits,” arXiv:2402.17764, 2024.

[15] M. Liu, N. Pinckney, B. Khailany, and H. Ren, “VerilogEval: Evaluating Large Language Models for Verilog Code Generation,” in Proceedings of ICCAD, 2023.

[16] Y. Lu, S. Liu, Q. Zhang, and Z. Xie, “RTLLM: An Open-Source Benchmark for Design RTL Generation with Large Language Model,” in Proceedings of ASP-DAC, 2024.

[17] S. Thakur et al., “VeriGen: A Large Language Model for Verilog Code Generation,” ACM Transactions on Design Automation of Electronic Systems, 2024.

[18] S. Liu, W. Fang, Y. Lu, Q. Zhang, H. Zhang, and Z. Xie, “RTLCoder: Outperforming GPT-3.5 in Design RTL Generation with an Open-Source Dataset and Lightweight Solution,” in Proceedings of LAD, 2024.

[19] B. Hui et al., “Qwen2.5-Coder Technical Report,” arXiv:2409.12186, 2024.

[20] M. Liu, Y.-D. Tsai, W. Zhou, and H. Ren, “CraftRTL: High-Quality Synthetic Data Generation for Verilog Code Models,” arXiv:2409.12993, 2024.

[21] E. Hu et al., “LoRA: Low-Rank Adaptation of Large Language Models,” in Proceedings of ICLR, 2022.

[22] Z. Shao et al., “DeepSeekMath: Pushing the Limits of Mathematical Reasoning in Open Language Models,” arXiv:2402.03300, 2024.

[23] N. Wang, B. Yao, J. Zhou, X. Wang, Z. Jiang, and N. Guan, “Large Language Model for Verilog Generation with Code-Structure-Guided Reinforcement Learning,” arXiv:2407.18271, 2024.

[24] Y. Zhao, W. Fu, S. Li, Y.-X. Hu, X. Guo, and Y. Jin, “Hardware Generation with High Flexibility Using Reinforcement Learning Enhanced LLMs,” in Proceedings of DAC, 2025.

[25] Z. Chen et al., “ChipSeek-R1: Generating Human-Surpassing RTL with LLM via Hierarchical Reward-Driven Reinforcement Learning,” arXiv:2507.04736, 2025.

[26] Y. Lu, S. Liu, H. Zhou, W. Fang, Q. Zhang, and Z. Xie, “A New Benchmark for the Appropriate Evaluation of RTL Code Optimization,” arXiv:2601.01765, 2026.

[27] W. Fang et al., “Dr. RTL: Autonomous Agentic RTL Optimization through Tool-Grounded Self-Improvement,” arXiv:2604.14989, 2026.

[28] W. Fang et al., “Transferable Pre-Synthesis PPA Estimation for RTL Designs With Data Augmentation Techniques,” IEEE Transactions on Computer-Aided Design of Integrated Circuits and Systems, vol. 44, no. 1, pp. 200-213, 2025.

[29] L. Gao, J. Schulman, and J. Hilton, “Scaling Laws for Reward Model Overoptimization,” in Proceedings of ICML, 2023.

[30] S. Williams, A. Waterman, and D. Patterson, “Roofline: An Insightful Visual Performance Model for Multicore Architectures,” Communications of the ACM, vol. 52, no. 4, pp. 65-76, 2009.
