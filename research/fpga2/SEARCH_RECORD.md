# FPGA2 — Search and decision record

Date: 2026-09-22. Output: [master reference](../../MASTER_REFERENCE.md) and [related-work ledger](RELATED_WORK.md).

## Search scope

The user requested two stages: first establish a mathematically modified transformer block with lower data movement and simpler hardware at preserved quality; then distill an LLM into it and apply the submitted paper's physical-reward fine-tuning approach. RFT-LM should be used only if it serves that objective.

Searches covered primary research in structured linear maps/FFNs, transformer FPGA co-design, fusion and memory scheduling, hardware-aware architecture search, low-rank/shared projections, numerical representations, small-model distillation, and optional external memory. Sources were primary paper pages, proceedings, author-hosted manuscripts, and author-maintained repositories. Aggregator summaries and Reddit were not treated as evidence.

Representative query groups executed:

| Theme | Query terms |
|---|---|
| Structural mathematics | `transformer block co design reduce data movement structured matrices accelerator Monarch`; `transformer architecture hardware co design block circulant butterfly`; `Learning Fast Algorithms for Linear Transforms`; `Monarch Mixer` |
| FPGA precedents | `FTRANS transformer FPGA`; `transformer butterfly FPGA accelerator`; `FlightLLM`; `LUT-LLM`; `ELiTeFormer` |
| Grouping and shared factors | `transformer grouped feed-forward hardware`; `transformer block-diagonal feed FPGA`; `LLM shared basis gate low rank`; `Basis Sharing`; `SkipCat`; `LatentLLM junction matrices`; `SVD-LLM` |
| Memory implementation | `transformer block fusion feed forward attention memory traffic`; `FLAT Fused attention accelerator`; `TransFusion End-to-End Transformer`; `Monarch bank accelerator`; `structured transformer data movement 2026` |
| Model/hardware search | `HAT Hardware-Aware Transformers`; `TransCODE Transformer co design`; LLMForge and Quasar-ViT primary pages |
| Distillation | `MiniLLM knowledge distillation`; `Minitron pruning distillation` |
| Optional memory | `Memorizing Transformers`; `Native Sparse Attention`; `external memory retrieval language model FPGA sparse routing top k` |
| ASIC path | `OpenROAD open-source RTL GDSII flow` |

The literature ledger contains **32 records**, with grouped closely related versions in some records. It is selective, not a count of every search hit. Coverage includes 2026 papers found during the search, but is not a guarantee of complete coverage through that date.

## Full-text checks that changed the recommendation

1. FABNet already studies memory-bank conflicts and custom data layout. Removed the potential claim that structured-transformer accelerators ignore banking.
2. SkipCat explicitly shares projections for gate/up and Q/K/V inputs and reports GPU timing. Rejected simple shared-input low-rank projection as a novel contribution.
3. TransFusion covers full-layer dependencies and scheduling. Rejected the claim that previous fusion work is only attention-local.
4. GroupBERT already uses grouped feed-forward transformations. Kept grouping as a baseline/test family.
5. Compute-in-memory work also maps sparse block-diagonal LLMs. Avoided presenting structured sparsity plus memory locality as an untouched field.
6. LLMForge includes measured and modeled backends. Kept the evidence types distinct and avoided a broad claim of novel small-LM hardware-aware search.

## Sources and versions needing further work

- An abstract supports the summarized contribution, but not a claim that the full paper lacks a feature. `A` entries need full-method review before implementation or exclusion.
- TransFusion's author-hosted PDF labels MICRO 2025 but includes placeholder publication fields; verify publisher metadata before a formal bibliography.
- MatMul-free LM changed deployment discussion across revisions; pin one version for any numerical comparison.
- MiniLLM and HSA have changed titles across versions; use stable identifiers plus the selected version.
- The selected Monarch HTML URL failed to load; its primary abstract was used. Obtain and read the PDF before selecting its exact operator variant.
- Inspect current code availability and license independently of a paper's code-release statement. No baseline repository was installed or executed for this review.
- Continue backward/forward citation checks for the specific selected block, including factor-layout constraints, grouped/shuffled FFNs, and nonlinear fusion. Do this before making a novelty claim.

## Local evidence used

The original workspace's `MASTER_REFERENCE.md` supplied historical infrastructure and paper-method context. The two user-named PDFs were read in this conversation and hashed; exact hashes and the distinction from the inherited GitHub artifact are in the new master reference.

The user's RFT-LM description was treated as reported prior-project evidence. Its source code, dataset boundaries, checkpoint contents, router inference semantics, and measurements have not been audited here. It is neither an imported dependency nor a confirmed FPGA2 baseline.

Read-only server checks earlier in this conversation established GPU model/count/memory. No GPU job, Vivado run, board reconfiguration, package installation, or ASIC run was launched to prepare these documents.

## Decisions

- Preserve the supervisor's two-stage sequence.
- Begin with a profiled, communication-constrained structured FFN hypothesis inside a fixed causal transformer.
- Require strong dense-fusion and existing structured baselines; include cost of permutations, buffers, and nonlinear boundaries.
- Defer RFT memory. Reuse evaluation lessons and audit reusable infrastructure later.
- Keep model-inference efficiency separate from generated-circuit utility during Stage 2.
- Treat the gap as provisional. A full reproduction/novelty audit can narrow, redirect, or invalidate it.
- Create `FPGA2` from the verified GitHub `main` snapshot in an isolated worktree; preserve the original working branch and uncommitted manuscript changes.
