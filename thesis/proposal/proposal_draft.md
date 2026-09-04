# 1  Source, Objectives, and Significance of the Research Project

## 1.1 Source of the Research Project

Proposed thesis title: Hardware-Aware LLM Architectures for FPGA RTL Generation: Inference Efficiency and Failure-Aware Utility under Fixed Budgets.

This project originates from supervisor-directed research on hardware-friendly large language models (LLMs), electronic design automation (EDA), and the physical evaluation of LLM-generated register-transfer-level (RTL) code. It builds on the author's completed work on correctness-gated policy optimization for streaming-accelerator RTL. That work produced a functioning pipeline for natural-language specifications, parameter-efficient model adaptation, executable verification, Vivado implementation, and limited PYNQ-Z2 measurement.

The proposed thesis is not a second full RTL-optimization project added to a separate LLM benchmark. The completed RTL pipeline is the measurement foundation. The new research question is narrower: when several available LLM systems are used to generate the same FPGA RTL tasks, does lower model-side inference cost translate into more correct and physically useful designs under realistic compute and EDA limits?

The two hardware layers are intentionally distinct. The LLM inference experiments will run on an NVIDIA GPU. The generated RTL will be implemented on an FPGA. The thesis will not claim that the LLM itself is deployed on the FPGA, and it will not experimentally generalize results to ASICs or NPUs. Those platforms will appear only in related work and future-work discussion.

The project is an independent academic study for the author's master's degree at Harbin Institute of Technology, Shenzhen. It uses existing laboratory computing, software, and FPGA resources. No commercial deliverable, external grant, or publication acceptance is assumed.

## 1.2 Research Objective and Questions

The overall objective is to establish and apply a reproducible, quality-constrained method for selecting an LLM system for FPGA RTL generation when model inference, functional verification, and physical implementation all consume a limited budget.

In this thesis, “hardware-aware” is an operational and platform-dependent term. An LLM configuration is hardware-aware for task set D on platform P only when its measured inference cost is interpreted together with the quality and physical usefulness of its generated RTL. Architectural complexity alone is not sufficient evidence of hardware efficiency.

The thesis will answer three core research questions:

- RQ1: On the same L40S GPU and under a common BF16 baseline, how do a dense grouped-query-attention Transformer, a pure Mamba-2 state-space model, and a hybrid attention-state-space model differ in prefill latency, decoding latency, throughput, peak memory, GPU energy, and measured arithmetic intensity across feasible context lengths and batch sizes?
- RQ2: After comparable parameter-efficient adaptation, how do the three systems differ in RTL extraction and compilation rate, functional pass@1 and pass@k, output length, failure modes, and post-route FPGA timing and resource use under equal sampling?
- RQ3: Under fixed generation time and fixed EDA budgets, which system yields the most functionally correct, implementable, and physically useful RTL, and at what quality, area, and specialization cost?

RQ1 is an enabling systems measurement. RQ2 and RQ3 form the main thesis contribution because they connect model-side efficiency to downstream FPGA outcomes. No hypothesis requires one architecture to win every condition.

## 1.3 Formal Evaluation Framework

Definition 1 (hardware-aware RTL-generation configuration). A configuration c consists of a frozen model checkpoint, tokenizer, inference engine, numerical precision, decoding policy, and target platform. For a declared task set D and quality requirement tau, c is efficiency-superior to a reference only if the quality difference satisfies the declared non-inferiority rule and at least one measured cost is lower without an undeclared resource increase.

For model m, task d, and N generated samples, let I_func(i) indicate that sample i passes the frozen executable oracle and I_impl(i) indicate that it completes the frozen FPGA implementation flow. Let F_i denote the explicitly labelled post-route frequency metric for sample i. Three quantities will be reported together:

EQ: q(m,d) = (1/N) Σ_i I_func(i) I_impl(i)

EQ: μ_F(m,d) = [Σ_i I_func(i) I_impl(i) F_i] / [Σ_i I_func(i) I_impl(i)]

EQ: U_F(m,d) = q(m,d) μ_F(m,d) = (1/N) Σ_i I_func(i) I_impl(i) F_i

Here q is usable yield, μ_F is frequency conditional on a usable implementation, and U_F is failure-penalized one-draw utility. Reporting all three prevents U_F from hiding whether a difference comes from yield or conditional timing. The metric does not replace the normal engineering workflow of selecting a survivor. That workflow is measured separately:

EQ: V_F(m,d;B) = max({F_i : i is verified within budget B} ∪ {0})

V_F is the best verified frequency obtained within budget B and is zero when the budget produces no usable design. U_F asks whether the generation distribution improved; V_F asks what a bounded search workflow can deliver. Area, power, and timing will be reported as a Pareto set rather than collapsed into an arbitrary universal PPA score.

## 1.4 Innovation Points

The proposed thesis has three explicit innovation points:

- A dual-layer evaluation framework that joins GPU inference cost with executable and post-route FPGA outcomes while decomposing usable yield, conditional physical quality, and failure-penalized utility.
- A tokenization-aware, quality-constrained protocol for comparing available dense, state-space, and hybrid LLM systems without misrepresenting an end-to-end model comparison as a causal architecture ablation.
- A fixed-budget decision analysis that measures correct and implemented RTL per GPU-hour, per measured GPU joule when telemetry is reliable, and per limited number of EDA runs, thereby identifying when faster inference creates engineering value and when verification or implementation becomes the bottleneck.

These are methodological and empirical innovations. The thesis will not claim a new foundational sequence architecture or a theorem about Transformer and state-space expressiveness.

# 2  Current Research Status and Analysis at Home and Abroad

## 2.1 Hardware-Efficient LLM Architectures

The Transformer established attention-based sequence modelling as the dominant language-model architecture [1]. During prefill, conventional self-attention forms pairwise interactions whose arithmetic and intermediate-state cost grows quadratically with sequence length. During autoregressive decoding, key-value (KV) caching avoids recomputation but creates a state that grows with context length and must be accessed for each new token.

Multi-query attention shares key and value heads [2], while grouped-query attention (GQA) provides an intermediate design between multi-head and multi-query attention [3]. FlashAttention retains exact attention but tiles the computation to reduce transfers between high-bandwidth memory and on-chip SRAM [4]. PagedAttention and vLLM address KV-cache fragmentation and serving-level memory management [5]. DeepSeek-V2's Multi-head Latent Attention compresses the KV representation [6], and Native Sparse Attention combines compressed, selected, and local attention with hardware-oriented blocking [7]. These methods show why nominal FLOP count alone cannot predict realized latency.

State-space models provide a different sequence operator. Mamba introduced input-dependent selective state updates and a hardware-aware scan implementation [8]. Mamba-2 connected state-space models and structured attention through state-space duality and reported a faster core layer [9]. Hybrid models such as Jamba [10] and Falcon-H1 [12] combine attention and state-space blocks to trade content-based retrieval against recurrent-state efficiency. Mamba-Codestral-7B-v0.1 is a publicly available Mamba-2 code model [11], making a task-relevant pure state-space comparison feasible.

Other important directions include sparse mixture-of-experts models [13], native ternary-weight models such as BitNet b1.58 [14], MLA, and sparse attention. They are relevant to the broader hardware-friendly architecture landscape, but they will not be added to the core experiment. Their routing, active parameter counts, training recipes, and specialized kernels would expand the comparison beyond a defensible master's scope.

The Roofline model relates achieved operations per second to arithmetic intensity and hardware bandwidth [32]. It is useful for explaining memory-bound and compute-bound regimes, but it does not replace end-to-end measurement. Prefill, decoding, batch size, context length, kernel maturity, graph breaks, numerical precision, tokenizer, and stopping behaviour must all be recorded.

## 2.2 LLM-Based RTL Generation and Physical Evaluation

VerilogEval and RTLLM established executable benchmarks for natural-language-to-Verilog generation [16], [17]. VeriGen, RTLCoder, Qwen2.5-Coder, and CraftRTL showed that domain data, synthetic examples, and targeted adaptation can substantially improve RTL generation [15], [18]-[20]. LoRA makes task adaptation possible without updating all base-model weights [22]. The unbiased pass@k estimator used in code-generation evaluation was formalized in the Codex study [23].

Chinese and China-based research groups have contributed strongly to this area. RTLLM and RTLCoder were developed at HKUST [17], [19]; Qwen2.5-Coder provides open code models over several sizes [15]; DeepSeek introduced MLA and GRPO-related methods [6], [24]; PPA-RTL incorporates synthesis-derived preferences into training [26]; and VCodePPA provides a Chinese-published Verilog dataset with PPA annotations [21]. This domestic work is directly relevant to the proposed combination of model efficiency and physical design evidence.

Recent studies move beyond syntax and simulation. VeriSeek uses code-structure-guided reinforcement learning [25]. PPA-RTL and ChipSeek integrate physical-design objectives into LLM training [26], [27]. RTL-OPT provides an optimization benchmark with functional and PPA evaluation [28], while Dr. RTL uses tool-grounded critical-path feedback and iterative rewriting [29]. MasterRTL predicts PPA before synthesis to reduce tool cost [30]. These studies make physical evaluation increasingly important, but most answer a different question from this thesis: how to optimize or repair RTL, rather than how to choose among LLM systems under a shared end-to-end budget.

Learned physical proxies are useful because EDA is expensive, but optimizing a proxy can move the policy outside the proxy's reliable data region. Reward-model overoptimization has been studied directly in language models [31]. Therefore, any learned reward used in an optional optimization extension will remain a training signal only. Functional simulators and the frozen Vivado flow will be the reporting authorities.

## 2.3 Research Gap and Positioning

The audited literature provides architecture-level efficiency studies, functional RTL benchmarks, and PPA-oriented generation methods. It does not provide a directly reusable protocol that jointly compares dense, pure state-space, and hybrid LLM systems on the same GPU and then connects their measured cost to failure-aware post-route FPGA utility under fixed draw, time, energy, and EDA limits.

Four methodological gaps motivate the thesis:

- Cross-model throughput numbers are often compared despite different tokenizers, precisions, engines, contexts, and output lengths.
- Functional correctness is often the final endpoint even though a correct RTL module can still fail implementation or have poor timing.
- Best-of-N reporting measures a search pipeline, while a failure-penalized average measures a policy distribution; the two questions are frequently conflated.
- Faster token generation is useful only if it produces additional correct and implementable candidates before simulation or EDA becomes the dominant cost.

The thesis is positioned as a systems-and-methodology study, not as a claim that pretraining differences have been eliminated. Full-size checkpoints differ in data, tokenizer, parameter count, and optimization history. The result will answer “Which available system is preferable for this declared workflow?” Causal claims about attention versus state-space layers will not be made from that comparison.

# 3  Main Research Content and Research Plan

## 3.1 Scope and Deliverables

The guaranteed thesis and optional extensions are separated explicitly.

Table 1  Minimum viable thesis and stretch goals

| Scope | Included work | Status in degree plan |
|---|---|---|
| Core A | Common-condition inference benchmark for three frozen model systems at approximately 0.5K, 2K, and 8K context | Required |
| Core B | Comparable LoRA adaptation, two seeds per model, frozen accelerator evaluation, and VerilogEvalV2 control | Required |
| Core C | Outcome-independent FPGA subset, failure-aware post-route evaluation, and fixed-draw/time/EDA analysis | Required |
| Extension 1 | 32K context, architecture-native lower precision, or additional serving engines | Only after Core A-C are secure |
| Extension 2 | Compact matched models trained under the same tokenizer/data schedule for causal architecture study | Optional; not required for thesis validity |
| Extension 3 | Repeating policy optimization for every architecture | Optional; the completed policy study is preliminary evidence, not a required rerun |
| Extension 4 | Larger PYNQ-Z2 campaign, second FPGA family, or external board-power instrumentation | Optional external-validity work |

If time or compute becomes limited, extensions are removed in the listed order. The core will not be expanded with MoE, MLA, BitNet, speculative decoding, or a new quantization algorithm.

## 3.2 Model Selection and Fairness Protocol

The initial model candidates are shown below. Exact repository revisions and file hashes will be frozen after a loading and correctness pilot and before confirmatory generation.

Table 2  Primary model-system candidates and selection rationale

| Class | Initial checkpoint | Rationale and limitation |
|---|---|---|
| Dense GQA Transformer | Qwen2.5-Coder-7B base | Open code-specialized reference, mature Transformer kernels, approximately 7B parameters [15] |
| Pure state-space | Mamba-Codestral-7B-v0.1 | Open code model based on Mamba-2, approximately 7B parameters, no attention KV cache [11] |
| Hybrid attention-SSM | Falcon-H1-7B-Base | Public hybrid checkpoint supported by current frameworks; the host reports approximately 8B parameters despite the 7B family name [12] |

The full-size comparison is an end-to-end system comparison. Different pretraining corpora and tokenizers will be treated as properties of the deployable systems, not controlled variables. Model identities, licenses, parameter counts, tokenizer revisions, training provenance stated by the provider, and inference-engine versions will be recorded.

The common inference condition will use one NVIDIA L40S GPU, BF16 weights and activations, batch sizes 1 and 4, identical semantic prompts, identical stopping rules, and the same sampling parameters. A common PyTorch/Transformers execution path will be used only if all three models pass output-correctness and performance sanity checks. If one model requires its native engine, the native-engine result will be labelled as a system result and will not be used to claim a pure architectural effect.

Tokenizers make raw tokens per second non-equivalent across models. The thesis will therefore report native token throughput together with wall-clock time per prompt, input and output UTF-8 bytes, characters per second, generated RTL length, and time/energy per verified result. No model will receive repeated filler text merely to reach a context target.

Comparable adaptation will use the same oracle-verified corpus, data split, examples, token-update budget, maximum sequence length, and two random seeds per architecture. LoRA target modules may differ because the layer structures differ; the exact modules and trainable-parameter fraction will be reported and kept as close as technically possible. Hyperparameter selection is restricted to a small development split and will be frozen before final evaluation.

A model passes the competence gate if, on five development tasks excluded from the final split, it achieves at least 80% extraction-plus-compilation, at least 30% functional pass@1, and at least one correct sample on four of five tasks using twenty samples. One predeclared adaptation retry is permitted. A model that still fails remains in RQ1 and the functional failure report but does not consume the physical-evaluation budget. It will not be silently replaced after final outcomes are seen.

## 3.3 Inference and Roofline Measurement

The core context bands are approximately 512, 2,048, and 8,192 native tokens, constructed from meaningful hardware-project material: specifications, interface definitions, verification requirements, and related modules. Exact native-token and byte counts will be reported for every model. A 32,768-token condition is an extension and proceeds only if all eligible models fit memory and finish the repeatability pilot.

Prefill and decoding will be measured separately. Each condition will use at least five warm-up iterations and twenty timed repetitions with explicit GPU synchronization. If the coefficient of variation of wall-clock latency exceeds 5%, measurement will extend to fifty repetitions and the instability will be reported. GPU clocks, temperature, driver, CUDA, framework, kernel, and engine versions will be recorded.

Primary model-side metrics are time to first token, prefill latency, inter-token latency, end-to-end completion latency, native tokens per second, bytes per second, peak allocated and reserved memory, cache or recurrent-state bytes, and maximum feasible batch size. NVML will collect GPU power and total-energy counters where supported [33]. Energy runs will last at least sixty seconds after warm-up to reduce telemetry quantization and averaging error. Gross GPU energy and idle-adjusted dynamic energy will be reported separately; neither is system-wall energy.

Energy becomes a fixed-budget result only if five repeated measurements have a coefficient of variation no greater than 5% and the device reports a supported counter. Otherwise it is a descriptive secondary metric. Board energy is outside the core scope.

Nsight Compute will profile representative prefill and decode conditions and provide measured DRAM traffic, achieved operations per second, arithmetic intensity, Tensor Core use, occupancy, and major stalls [34]. The Roofline interpretation will be tied to those measured kernels rather than inferred from asymptotic complexity alone [32]. Graph capture, graph breaks, kernel count, fallbacks, and failed operator fusion will be preserved as results.

## 3.4 Functional RTL Evaluation

A new twenty-design accelerator split will be frozen before final model outputs are generated. It will contain four designs from each of the five existing families: FIR, reverse FIR, polynomial, IIR, and median filter. The split will balance interpolation and extrapolation within each family where the generator contract permits. Every final task will be excluded from the adaptation corpus and development gate, and a contamination report will be generated before inference.

For each model and task, two adapted seeds will each generate ten samples, giving N=20 samples per model-task. The decoding seed, temperature, top-p, maximum length, prompt, and stopping rule will be fixed. On VerilogEvalV2's 156 tasks [16], each adapted seed will generate five samples, giving ten samples per model-task. Functional pass@1, pass@5, and pass@10 will use the unbiased estimator [23]. Seed-specific point estimates will also be shown.

Extraction failure, syntax failure, simulator failure, functional mismatch, unknown-value contamination, timeout, and successful verification will remain separate outcomes. The final accelerator oracle will use directed corner cases plus two independent 1,024-vector randomized streams. It will search only a frozen, specification-permitted latency window. Exact post-alignment equality will be the confirmatory rule; the older 0.999 trace threshold belongs only to the preliminary study. Known-correct reference implementations and mutation tests will be used to audit the oracle before the split is opened.

The oracle is sampled evidence, not formal equivalence. This residual risk will be stated. Formal checking of a small subset is an extension if suitable properties and tools are available.

## 3.5 FPGA Physical Evaluation

Before generation, ten of the twenty final accelerator tasks will be selected by a reproducible hash rule, with two tasks per family and interpolation/extrapolation balance where possible. For each selected task, the first five frozen sample identifiers from each adaptation seed will enter the physical phase. This gives ten draws per model-task and a hard maximum of 300 candidate draws across three models and ten tasks.

Every distinct oracle-correct candidate among those draws will be implemented once in AMD Vivado 2026.1 for the Xilinx Zynq-7020 target. Original multiplicity will then be restored for q, μ_F, and U_F. Incorrect and implementation-failed draws remain zero in U_F. The maximum campaign size is therefore known before outcomes: no more than 300 unique Vivado implementations. Planning assumes at most fifty completed implementations per week, giving six weeks of schedule capacity; lower observed throughput triggers schedule reduction of optional work, not outcome-dependent candidate removal.

The all-candidate metric will be labelled post-route WNS-derived frequency, not true timing closure. A preregistered subset of thirty candidates spanning low, middle, and high WNS-derived values across model classes and families will undergo the already validated bounded timing-closure search. Correlation, rank stability, relative error, and paired sign reversals will be reported. This subset bounds the approximation; it does not retrospectively convert all historical values into timing-closed measurements.

The physical report will include LUTs, flip-flops, DSPs, BRAMs, implementation success, WNS, the timing metric, and Vivado vectorless estimated power. Vectorless power will be labelled as a tool estimate with its activity assumptions and will not be presented as measured board power. Conditional PPA is reported only on comparable usable support, alongside the failure-aware primary quantities.

## 3.6 Fixed-Budget and Statistical Analysis

The principal budgets are fixed before final evaluation as follows.

Table 3  Core budgets and sensitivity levels

| View | Primary budget | Sensitivity analysis |
|---|---|---|
| Equal functional draws | 20 samples per model-task, 10 per adaptation seed | 10 and 20 draws |
| Equal physical draws | 10 preassigned samples per model-task, all distinct correct candidates implemented | 5 and 10 draws |
| Equal generation time | T0 per task, where T0 is frozen as the slowest eligible model's pilot time for 20 common-condition samples | 0.5T0, T0, and 2T0 |
| Equal GPU energy | E0 defined analogously from the frozen pilot only if the telemetry gate passes | 0.5E0, E0, and 2E0 |
| Equal EDA budget | First K distinct correct candidates in frozen hash order, K=3 per model-task | K=1, 3, and 5 |
| Academic workflow scenario | 10 L40S GPU-hours and 50 Vivado implementations allocated by frozen round-robin task order | 5/20 GPU-hours and 25/100 implementations |

Fixed-time and fixed-energy analysis allows faster systems to generate more candidates. Fixed-EDA analysis prevents unlimited synthesis or implementation from hiding the cost of candidate selection. Generation and EDA order will be determined by frozen identifiers, not observed frequency.

Quality-constrained comparisons use the dense GQA system as the reference. For the accelerator split, the primary non-inferiority margin is 5 absolute percentage points in pass@1; for VerilogEvalV2 it is 3 points. A candidate system is non-inferior only if the lower bound of the paired 95% interval for its difference from the reference exceeds the negative margin. Sensitivity at 2, 5, and 10 points will be shown. The two planned comparisons against the reference will use Holm adjustment.

Primary uncertainty will use paired task-level bootstrap intervals with 10,000 resamples. The interval quantifies variation across the declared tasks and samples; it does not represent all possible pretraining corpora or model families. With only two adaptation seeds, seed-specific effects are directional robustness points rather than a precise estimate of training-seed variance. Family and interpolation/extrapolation summaries are descriptive unless their cell sizes support a declared interval.

The analysis will report Pareto frontiers instead of a single universal efficiency score. In addition to q, μ_F, U_F, and V_F, outputs include correct RTL per GPU-hour, usable implementations per GPU-hour, usable implementations per measured GPU joule when valid, and best verified timing within an EDA budget. Canonical structural-feature distance, output length, and entropy will be used as secondary distribution-shift diagnostics, not as correctness evidence.

## 3.7 Research Workflow

Table 4  Research workflow and decision gates

| Stage | Main operation | Frozen output or gate |
|---|---|---|
| 1 | Finalize scope, model candidates, metrics, budgets, and reference audit | Versioned protocol and proposal |
| 2 | Load models and test common BF16 inference on L40S | Frozen checkpoint hashes, engines, and feasible context bands |
| 3 | Run inference and telemetry pilot | Repeatability gate, T0, and conditional E0 |
| 4 | Adapt two seeds per architecture using the same corpus and token budget | Competence-gated adapters and full provenance |
| 5 | Freeze new tasks and complete contamination/oracle audits | Unopened final split and oracle audit |
| 6 | Generate all samples and run functional evaluation | Failure-complete functional dataset and pass@k results |
| 7 | Implement the preassigned ten-task physical subset | Post-route dataset, timing-closure sensitivity subset, and PPA report |
| 8 | Compute equal-draw and fixed-budget comparisons | Paired intervals, Pareto plots, and deployment regime map |
| 9 | Complete thesis, claim ledger, artifact, and defense | Reproducible thesis package |

# 4  Expected Objectives

## 4.1 Minimum Success Criteria

The thesis will be considered successfully completed when it delivers all of the following, regardless of which architecture ranks first:

- A frozen, reproducible inference benchmark for three eligible dense, state-space, and hybrid model systems on one L40S GPU at the three core context bands.
- A transparent model manifest containing checkpoint revisions, tokenizers, licenses, engines, precision, trainable parameters, and adaptation seeds.
- Functional results on a new unopened five-family accelerator split and VerilogEvalV2 with all failures retained.
- Post-route results for the preassigned ten-task FPGA subset within the 300-run ceiling, plus a bounded timing-closure sensitivity study.
- Separate usable-yield, conditional-frequency, failure-penalized, and budgeted-best results rather than one ambiguous score.
- A fixed-budget regime map showing when inference, functional verification, or EDA is the limiting resource.
- A versioned artifact with prompts, manifests, hashes, raw measurements, analysis scripts, stopped-run records, and claim-to-artifact provenance.

No unsupported numerical target is imposed on the hybrid or state-space models. A negative result—for example, faster decoding accompanied by inadequate RTL quality—is a valid thesis finding if obtained under the frozen protocol.

## 4.2 Expected Academic and Engineering Outputs

The academic output will be a master's thesis that contributes an operational framework, a reproducible benchmark protocol, and empirical evidence for hardware-aware LLM system selection in FPGA RTL generation. The engineering output will be a practical decision procedure for choosing a model and candidate budget under limited GPU and EDA resources.

The completed policy-optimization study is currently being prepared as a separate research manuscript. It will be cited in the thesis as preliminary or related author work only after its status is stated accurately. The proposed cross-architecture results may support another manuscript submission if the evidence is sufficiently strong. Preparation or submission may be listed as dissemination, but paper acceptance is not promised and is not a condition for successful thesis completion.

# 5  Completed Research Work and Schedule

## 5.1 Completed Research Work

The core RTL evaluation infrastructure already exists. It includes prompt and design generators for five streaming-accelerator families, LoRA-based supervised fine-tuning, group-relative policy optimization, candidate extraction, Icarus Verilog compilation, a deterministic multi-seed functional oracle, content deduplication, Vivado synthesis and routing, resource extraction, bounded timing-closure search, and PYNQ-Z2 clock sweeps. Provenance controls include frozen manifests, hashes, completion audits, and fail-closed claim ledgers.

In a previously frozen twenty-design study, two policy-optimization runs with distinct RL seeds from one shared SFT checkpoint were compared with the SFT distribution. The seed-averaged failure-penalized post-route WNS-derived endpoint increased from 35.38 MHz to 93.01 MHz. The paired task-level gain was 57.64 MHz with a design-bootstrap 95% interval of [37.69, 77.20] MHz. This interval reflects task variation, not complete training-seed uncertainty. Correctness changed from 56.25% for SFT to 53.85% for the combined RF policies, so the endpoint did not obtain its gain by discarding failures.

System-level controls provide useful but bounded evidence. A repaired reward package using canonical structural features and a random forest outperformed the earlier uncanonicalized MLP package; because model class, features, and canonicalization changed together, the contrast does not identify a single causal component. A correctness-only run raised functional yield but lowered physical utility, but that control currently has only one completed seed. These limitations will be stated rather than hidden.

Conditional PPA showed that the timing improvement was not free: the optimized policy used more LUTs and flip-flops, fewer DSPs, and slightly higher Vivado vectorless power on common usable support. A five-pair PYNQ-Z2 experiment was amended for feasibility and produced two wins, two resolution-limited ties, and one loss. It is descriptive and non-confirmatory.

A later ten-candidate timing-closure pilot using Vivado 2026.1 completed all candidates. WNS-derived frequency and bounded closure frequency had pooled Spearman correlation 0.963 and median symmetric absolute percentage error about 3.5%; the five SFT/RF pairs had no non-tied sign reversal. This supports the planned closure-sensitivity design but does not replace a full twenty-design timing-closure evaluation.

A matched VerilogEvalV2 extension used 156 problems and twenty samples per problem. SFT pass@1 was 22.34%; the two RF policies obtained 21.12% and 20.77%. The seed-averaged difference was -1.39 percentage points with a paired interval [-2.69, -0.10]. The result is a small detectable general-RTL specialization cost and motivates explicit quality constraints in the new thesis.

A working manuscript, “Correctness-Gated Policy Optimization for FPGA Accelerator RTL: A Controlled Post-Route Study,” is in preparation. It is not an accepted publication and its title and claims may change after the ongoing replication and review work.

## 5.2 Research Schedule and Contingency

The schedule assumes proposal approval in September 2026 and a defense around June 2027. Official university dates will take precedence.

Table 5  Monthly schedule

| Period | Core work and deliverable | Contingency or extension rule |
|---|---|---|
| September 2026 | Submit proposal; consolidate preliminary paper evidence; freeze thesis definitions | No new thesis experiment before protocol review |
| October 2026 | Load the three checkpoints; verify licenses and hashes; build common L40S harness | Replace a model only before the freeze if it cannot run reproducibly |
| November 2026 | Complete inference pilot and core 0.5K/2K/8K measurements; freeze T0 and energy gate | Drop 32K and native-engine extensions first |
| December 2026 | Complete matched corpus preparation, two LoRA seeds per model, and competence gate | Permit one predeclared retry; retain any failed architecture in the report |
| January 2027 | Freeze the twenty-design split; run contamination and oracle audits; complete functional and VerilogEvalV2 generation | Reduce optional native-precision work if generation is delayed |
| February 2027 | Begin the ten-task physical campaign and all-candidate WNS-derived implementation | Maintain the 300-run ceiling and remove board work if throughput is low |
| March 2027 | Finish physical campaign and thirty-candidate timing-closure sensitivity; start fixed-budget analysis | Reserve the final week as EDA failure/retry slack |
| April 2027 | Complete statistics, Pareto analysis, regime map, and results chapters | PYNQ or second-device work proceeds only if all core tables are frozen |
| May 2027 | Complete full thesis draft, citation/claim audit, artifact documentation, and internal review | Manuscript submission is secondary to thesis completion |
| June 2027 | Incorporate feedback, finalize university formatting, and prepare defense | Core artifact and thesis remain the graduation deliverables |

# 6  Existing Research Conditions and Funding Assurance

## 6.1 Existing Conditions

Available computing resources include two 32 GB NVIDIA V100-class GPUs and authorized access to NVIDIA L40S GPUs. The L40S is the sole primary inference platform because it supports the common BF16 condition and current profiling tools. V100 results, if collected, will be labelled as a secondary portability check and will not be pooled with the L40S comparison.

The local FPGA environment includes AMD Vivado 2026.1 and a validated implementation flow for the Xilinx Zynq-7020 device. The PYNQ-Z2 board and measurement harness remain available for optional validation. Icarus Verilog provides inexpensive filtering before EDA. Existing software supports parameter-efficient adaptation, multi-sample generation, oracle evaluation, candidate deduplication, PPA extraction, timing-closure search, and statistical analysis.

The repository already contains structured manifests, frozen-hash checks, analysis scripts, Word and LaTeX document tooling, and version control. Model weights and large profiler traces will remain on authorized storage and will be identified by immutable hashes rather than copied into the thesis repository when licensing or size prevents redistribution.

## 6.2 Funding and Resource Limits

The minimum thesis does not require an H100 GPU, a new FPGA, paid commercial APIs, or external power instrumentation. Existing institutional and personal research resources are sufficient if L40S scheduling and the licensed Vivado installation remain available.

The physical campaign has a maximum of 300 unique candidate implementations and a six-week planning window. The absolute fixed-budget scenario uses 10 L40S GPU-hours and 50 Vivado runs, with declared sensitivity levels. Optional expenses such as storage, replacement cables, API baselines, a second FPGA, or a power meter require supervisor approval and cannot become dependencies of the core thesis.

If L40S access is interrupted, the project will first postpone optional 32K and native-kernel experiments. If interruption persists, the common comparison will move to a single available platform and precision supported by all eligible models, and the protocol change will be documented before outcomes are collected.

# 7  Anticipated Difficulties, Solutions, and Research Integrity

## 7.1 Main Risks and Mitigations

Cross-model fairness is the largest interpretive risk. The three available checkpoints differ in pretraining, tokenizer, exact parameter count, and kernel support. The mitigation is not to pretend these variables are controlled. The thesis will call the main experiment an end-to-end system comparison, record the differences, use identical semantic tasks and a common hardware condition, and limit causal architecture language to any separately matched extension.

Software maturity may favour the dense Transformer. Common-framework and native-engine conditions will therefore be separated. Unsupported kernels, compilation failures, graph breaks, and fallbacks are reportable results. A theoretical O(L) or O(L²) label will never be substituted for measured wall-clock behaviour.

Tokenization can distort throughput comparisons. Native tokens per second will be accompanied by bytes, characters, total completion time, and useful results per unit cost. Meaningful project context will be used at long lengths.

Energy telemetry is less precise than timing. The sixty-second measurement window, idle baseline, repeated-run gate, and CV threshold will determine whether fixed-energy conclusions are permitted. The claim is GPU-side energy only; no board- or whole-system energy claim will be made without external instrumentation.

EDA cost can dominate the workflow. The preassigned ten-task subset, ten physical draws per model-task, deduplication, and 300-run ceiling make the campaign finite. The K=1/3/5 budget analysis tests whether extra implementation runs change the recommendation.

Functional tests cannot prove universal equivalence. Directed and randomized stimuli, multiple seeds, exact comparison, mutation testing, and known-correct references reduce the risk, while the sampled-oracle limitation remains explicit. Formal verification is optional rather than silently implied.

Pretraining-data leakage cannot be ruled out because complete model corpora are unavailable. The final tasks will be newly generated and excluded from all local adaptation data, public-repository similarity will be checked where practical, and the thesis will distinguish local contamination control from unknowable upstream pretraining exposure.

Distribution shift and specialization will be monitored through VerilogEvalV2, canonical-feature distances, output length, entropy, and failure taxonomy. These diagnostics cannot override executable correctness.

Scope creep is controlled by Table 1. Training compact models from scratch, adding new acceleration algorithms, evaluating MoE/MLA/BitNet, 32K contexts, policy optimization for every architecture, board power, and a second FPGA are not required for the degree.

## 7.2 Reproducibility, Ethics, and Dissemination

Every confirmatory model revision, task split, prompt, seed, stopping rule, budget, oracle version, tool version, and analysis script will be frozen and hashed before the relevant outcomes are examined. Failed and stopped experiments will remain in the record. Empirical claims in the thesis will resolve to raw artifacts through a claim ledger.

Only public, institutionally authorized, or author-generated data will be used. Model and benchmark licenses will be recorded. No proprietary RTL, confidential company data, or undocumented third-party intellectual property will be intentionally included. Public release will exclude artifacts whose licenses prohibit redistribution and will instead provide identifiers and reproduction instructions.

Any generative-AI assistance used for language editing, coding support, or review will be disclosed according to university and publication policies. Such tools will not be treated as empirical or bibliographic authorities. The student and supervisor remain responsible for verifying every factual claim, citation, equation, experiment, and conclusion.

Research findings will be disseminated through the thesis, defense, and a reproducibility package. Manuscript submission is desirable when the evidence supports it, but submission or acceptance will not be represented as a guaranteed research outcome.

# References

[1] A. Vaswani et al., “Attention Is All You Need,” in Advances in Neural Information Processing Systems, vol. 30, 2017. Available: https://proceedings.neurips.cc/paper/2017/hash/3f5ee243547dee91fbd053c1c4a845aa-Abstract.html

[2] N. Shazeer, “Fast Transformer Decoding: One Write-Head Is All You Need,” arXiv:1911.02150, 2019. Available: https://arxiv.org/abs/1911.02150

[3] J. Ainslie, J. Lee-Thorp, M. de Jong, Y. Zemlyanskiy, F. Lebron, and S. Sanghai, “GQA: Training Generalized Multi-Query Transformer Models from Multi-Head Checkpoints,” in Proceedings of EMNLP, pp. 4895-4901, 2023, doi: 10.18653/v1/2023.emnlp-main.298.

[4] T. Dao, D. Y. Fu, S. Ermon, A. Rudra, and C. Re, “FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness,” in Advances in Neural Information Processing Systems, vol. 35, pp. 16344-16359, 2022.

[5] W. Kwon et al., “Efficient Memory Management for Large Language Model Serving with PagedAttention,” in Proceedings of the 29th ACM Symposium on Operating Systems Principles, pp. 611-626, 2023, doi: 10.1145/3600006.3613165.

[6] DeepSeek-AI et al., “DeepSeek-V2: A Strong, Economical, and Efficient Mixture-of-Experts Language Model,” arXiv:2405.04434, 2024. Available: https://arxiv.org/abs/2405.04434

[7] J. Yuan et al., “Native Sparse Attention: Hardware-Aligned and Natively Trainable Sparse Attention,” arXiv:2502.11089, 2025. Available: https://arxiv.org/abs/2502.11089

[8] A. Gu and T. Dao, “Mamba: Linear-Time Sequence Modeling with Selective State Spaces,” in Proceedings of the First Conference on Language Modeling, 2024. Available: https://openreview.net/forum?id=tEYskw1VY2

[9] T. Dao and A. Gu, “Transformers Are SSMs: Generalized Models and Efficient Algorithms Through Structured State Space Duality,” in Proceedings of the 41st International Conference on Machine Learning, PMLR 235, pp. 10041-10071, 2024.

[10] O. Lieber et al., “Jamba: A Hybrid Transformer-Mamba Language Model,” arXiv:2403.19887, 2024. Available: https://arxiv.org/abs/2403.19887

[11] Mistral AI, “Model Card for Mamba-Codestral-7B-v0.1,” Hugging Face, 2024. [Online]. Available: https://huggingface.co/mistralai/Mamba-Codestral-7B-v0.1. [Accessed: Sep. 4, 2026].

[12] J. Zuo et al., “Falcon-H1: A Family of Hybrid-Head Language Models Redefining Efficiency and Performance,” arXiv:2507.22448, 2025. Available: https://arxiv.org/abs/2507.22448

[13] W. Fedus, B. Zoph, and N. Shazeer, “Switch Transformers: Scaling to Trillion Parameter Models with Simple and Efficient Sparsity,” Journal of Machine Learning Research, vol. 23, no. 120, pp. 1-39, 2022.

[14] S. Ma et al., “The Era of 1-bit LLMs: All Large Language Models Are in 1.58 Bits,” arXiv:2402.17764, 2024. Available: https://arxiv.org/abs/2402.17764

[15] B. Hui et al., “Qwen2.5-Coder Technical Report,” arXiv:2409.12186, 2024. Available: https://arxiv.org/abs/2409.12186

[16] M. Liu, N. Pinckney, B. Khailany, and H. Ren, “Invited Paper: VerilogEval: Evaluating Large Language Models for Verilog Code Generation,” in Proceedings of ICCAD, pp. 1-8, 2023, doi: 10.1109/ICCAD57390.2023.10323812.

[17] Y. Lu, S. Liu, Q. Zhang, and Z. Xie, “RTLLM: An Open-Source Benchmark for Design RTL Generation with Large Language Model,” in Proceedings of ASP-DAC, pp. 722-727, 2024, doi: 10.1109/ASP-DAC58780.2024.10473904.

[18] S. Thakur et al., “VeriGen: A Large Language Model for Verilog Code Generation,” ACM Transactions on Design Automation of Electronic Systems, vol. 29, no. 3, Art. no. 46, 2024, doi: 10.1145/3643681.

[19] S. Liu et al., “RTLCoder: Fully Open-Source and Efficient LLM-Assisted RTL Code Generation Technique,” IEEE Transactions on Computer-Aided Design of Integrated Circuits and Systems, vol. 44, no. 4, pp. 1448-1461, 2025, doi: 10.1109/TCAD.2024.3483089.

[20] M. Liu, Y.-D. Tsai, W. Zhou, and H. Ren, “CraftRTL: High-Quality Synthetic Data Generation for Verilog Code Models with Correct-by-Construction Non-Textual Representations and Targeted Code Repair,” in Proceedings of ICLR, 2025. Available: https://proceedings.iclr.cc/paper_files/paper/2025/hash/e112a4671e8779aa9f640a0e3f81bd26-Abstract-Conference.html

[21] X. Chen, Y. Jiang, Y. Xia, J. Hu, and Y. Zhou, “VCodePPA: A Large-Scale Verilog Dataset with PPA Annotations,” Journal of Electronics & Information Technology, vol. 47, no. 11, pp. 4606-4619, 2025, doi: 10.11999/JEIT250449.

[22] E. J. Hu et al., “LoRA: Low-Rank Adaptation of Large Language Models,” in Proceedings of ICLR, 2022. Available: https://openreview.net/forum?id=nZeVKeeFYf9

[23] M. Chen et al., “Evaluating Large Language Models Trained on Code,” arXiv:2107.03374, 2021. Available: https://arxiv.org/abs/2107.03374

[24] Z. Shao et al., “DeepSeekMath: Pushing the Limits of Mathematical Reasoning in Open Language Models,” arXiv:2402.03300, 2024. Available: https://arxiv.org/abs/2402.03300

[25] N. Wang, B. Yao, J. Zhou, X. Wang, Z. Jiang, and N. Guan, “Large Language Model for Verilog Generation with Code-Structure-Guided Reinforcement Learning,” arXiv:2407.18271, 2024. Available: https://arxiv.org/abs/2407.18271

[26] Y. Zhao, W. Fu, S. Li, Y.-X. Hu, X. Guo, and Y. Jin, “Hardware Generation with High Flexibility Using Reinforcement Learning Enhanced LLMs,” in Proceedings of the 62nd ACM/IEEE Design Automation Conference, pp. 1-7, 2025, doi: 10.1109/DAC63849.2025.11132897.

[27] Z. Chen et al., “ChipSeek: Optimizing Verilog Generation via EDA-Integrated Reinforcement Learning,” in Proceedings of the 64th Annual Meeting of the Association for Computational Linguistics, vol. 1, pp. 25180-25201, 2026, doi: 10.18653/v1/2026.acl-long.1154.

[28] Y. Lu, S. Liu, H. Zhou, W. Fang, Q. Zhang, and Z. Xie, “A New Benchmark for the Appropriate Evaluation of RTL Code Optimization,” arXiv:2601.01765, 2026. Available: https://arxiv.org/abs/2601.01765

[29] W. Fang et al., “Dr. RTL: Autonomous Agentic RTL Optimization through Tool-Grounded Self-Improvement,” arXiv:2604.14989, 2026. Available: https://arxiv.org/abs/2604.14989

[30] W. Fang et al., “Transferable Presynthesis PPA Estimation for RTL Designs with Data Augmentation Techniques,” IEEE Transactions on Computer-Aided Design of Integrated Circuits and Systems, vol. 44, no. 1, pp. 200-213, 2025, doi: 10.1109/TCAD.2024.3420904.

[31] L. Gao, J. Schulman, and J. Hilton, “Scaling Laws for Reward Model Overoptimization,” in Proceedings of the 40th International Conference on Machine Learning, PMLR 202, pp. 10835-10866, 2023.

[32] S. Williams, A. Waterman, and D. Patterson, “Roofline: An Insightful Visual Performance Model for Multicore Architectures,” Communications of the ACM, vol. 52, no. 4, pp. 65-76, 2009, doi: 10.1145/1498765.1498785.

[33] NVIDIA, “NVML API Reference Guide.” [Online]. Available: https://docs.nvidia.com/deploy/nvml-api/. [Accessed: Sep. 4, 2026].

[34] NVIDIA, “Nsight Compute Profiling Guide.” [Online]. Available: https://docs.nvidia.com/nsight-compute/ProfilingGuide/. [Accessed: Sep. 4, 2026].
