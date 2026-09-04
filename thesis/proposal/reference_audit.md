# Proposal Reference Audit

Audit date: 2026-09-04

Scope: existence, title, authorship at the abbreviated level used in the proposal, venue/status, year, and persistent identifier or official record. The audit verifies that a source is real; it does not treat every claim made by that source as independently established.

Result: all 34 references retained in `proposal_draft.md` resolve to real primary publication records, author-hosted model records, or official tool documentation. Preprints, model cards, and vendor documentation are labelled below and must not be described as peer-reviewed papers.

| Ref. | Verification record | Source type and audit result |
|---|---|---|
| [1] | [NeurIPS proceedings](https://proceedings.neurips.cc/paper/2017/hash/3f5ee243547dee91fbd053c1c4a845aa-Abstract.html) | Peer-reviewed conference paper; verified |
| [2] | [arXiv:1911.02150](https://arxiv.org/abs/1911.02150) | Preprint; verified |
| [3] | [ACL Anthology](https://aclanthology.org/2023.emnlp-main.298/) | Peer-reviewed EMNLP paper; DOI and pages verified |
| [4] | [NeurIPS proceedings](https://proceedings.neurips.cc/paper_files/paper/2022/hash/67d57c32e20fd0a7a302cb81d36e40d5-Abstract.html) | Peer-reviewed conference paper; pages verified |
| [5] | [ACM DOI record](https://doi.org/10.1145/3600006.3613165) | Peer-reviewed SOSP paper; DOI and pages verified |
| [6] | [arXiv:2405.04434](https://arxiv.org/abs/2405.04434) | Technical report/preprint; verified |
| [7] | [arXiv:2502.11089](https://arxiv.org/abs/2502.11089) | Preprint; verified |
| [8] | [OpenReview COLM record](https://openreview.net/forum?id=tEYskw1VY2) | Peer-reviewed COLM paper; verified |
| [9] | [PMLR record](https://proceedings.mlr.press/v235/dao24a.html) | Peer-reviewed ICML paper; volume and pages verified |
| [10] | [arXiv:2403.19887](https://arxiv.org/abs/2403.19887) | Technical report/preprint; verified |
| [11] | [Mistral AI model card](https://huggingface.co/mistralai/Mamba-Codestral-7B-v0.1) | Official model card, not a peer-reviewed paper; model family, size, precision, and license verified |
| [12] | [arXiv:2507.22448](https://arxiv.org/abs/2507.22448) | Technical report/preprint; verified |
| [13] | [JMLR record](https://jmlr.org/papers/v23/21-0998.html) | Peer-reviewed journal paper; volume, article number, and pages verified |
| [14] | [arXiv:2402.17764](https://arxiv.org/abs/2402.17764) | Preprint; verified |
| [15] | [arXiv:2409.12186](https://arxiv.org/abs/2409.12186) | Technical report/preprint; verified |
| [16] | [IEEE DOI record](https://doi.org/10.1109/ICCAD57390.2023.10323812) | Peer-reviewed ICCAD paper; DOI verified |
| [17] | [IEEE DOI record](https://doi.org/10.1109/ASP-DAC58780.2024.10473904) | Peer-reviewed ASP-DAC paper; DOI and pages verified |
| [18] | [ACM DOI record](https://doi.org/10.1145/3643681) | Peer-reviewed ACM TODAES article; volume, issue, and article number verified |
| [19] | [IEEE DOI record](https://doi.org/10.1109/TCAD.2024.3483089) | Peer-reviewed IEEE TCAD article; volume, issue, and pages verified |
| [20] | [Official ICLR proceedings](https://proceedings.iclr.cc/paper_files/paper/2025/hash/e112a4671e8779aa9f640a0e3f81bd26-Abstract-Conference.html) | Peer-reviewed ICLR paper; title and authors verified |
| [21] | [Journal of Electronics & Information Technology](https://www.jeit.ac.cn/en/article/doi/10.11999/JEIT250449) | Peer-reviewed Chinese journal article; bilingual title, DOI, volume, issue, and pages verified |
| [22] | [OpenReview ICLR record](https://openreview.net/forum?id=nZeVKeeFYf9) | Peer-reviewed ICLR paper; verified |
| [23] | [arXiv:2107.03374](https://arxiv.org/abs/2107.03374) | Technical report/preprint; verified |
| [24] | [arXiv:2402.03300](https://arxiv.org/abs/2402.03300) | Technical report/preprint; verified |
| [25] | [arXiv:2407.18271](https://arxiv.org/abs/2407.18271) | Preprint; current v4 title and authors verified |
| [26] | [IEEE Xplore record](https://ieeexplore.ieee.org/document/11132897/) | Peer-reviewed DAC paper; DOI, authors, year, and pages verified |
| [27] | [ACL Anthology](https://aclanthology.org/2026.acl-long.1154/) | Peer-reviewed ACL 2026 long paper; current title, DOI, and pages verified |
| [28] | [arXiv:2601.01765](https://arxiv.org/abs/2601.01765) | Preprint; title and authors verified |
| [29] | [arXiv:2604.14989](https://arxiv.org/abs/2604.14989) | Preprint; title and authors verified |
| [30] | [IEEE DOI record](https://doi.org/10.1109/TCAD.2024.3420904) | Peer-reviewed IEEE TCAD article; DOI, volume, issue, and pages verified |
| [31] | [PMLR record](https://proceedings.mlr.press/v202/gao23h.html) | Peer-reviewed ICML paper; volume and pages verified |
| [32] | [ACM DOI record](https://doi.org/10.1145/1498765.1498785) | Communications of the ACM article; DOI, volume, issue, and pages verified |
| [33] | [NVIDIA NVML documentation](https://docs.nvidia.com/deploy/nvml-api/) | Official vendor documentation, not a paper; verified |
| [34] | [NVIDIA Nsight Compute guide](https://docs.nvidia.com/nsight-compute/ProfilingGuide/) | Official vendor documentation, not a paper; verified |

## Corrections made during the audit

- Replaced an unverified CraftRTL OpenReview identifier with the official ICLR 2025 proceedings record.
- Updated VeriSeek reference [25] to its current arXiv v4 title, “Large Language Model for Verilog Generation with Code-Structure-Guided Reinforcement Learning.”
- Updated ChipSeek reference [27] from its older preprint title to the final ACL 2026 title and proceedings record.
- Expanded VeriGen, FlashAttention, and PagedAttention metadata with the verified issue/article or page information.
- Retained Mamba-Codestral as a model card and NVIDIA measurement sources as documentation; the proposal does not mislabel them as peer-reviewed research.
- Did not add the reviewer-suggested “LeCun et al., 2024 on hardware-aware LLMs,” because no precise, relevant bibliographic record was supplied or safely identifiable. An uncertain citation is worse than a shorter verified bibliography.
