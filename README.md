# FPGA2 — Transformer architecture and chip co-design

This branch starts the next research project: first test transformer block
structures that reduce data movement and simplify an accelerator while preserving
model quality; then distill an LLM into the selected architecture and adapt it for
physically useful RTL generation.

Start with the [FPGA2 master reference](MASTER_REFERENCE.md), the
[related-work ledger](research/fpga2/RELATED_WORK.md), and the
[search and decision record](research/fpga2/SEARCH_RECORD.md).
The [Stage 1 execution report](research/fpga2/STAGE1_STATUS.md) records the first
bounded pilots, and [stage1/README.md](stage1/README.md) gives the code and protocol.
These are preliminary pipeline checks, not evidence of a new efficient architecture.

The previous paper's reviewer artifact is retained below and in its existing
directories. Its results are distinct from the proposed FPGA2 research.

---

# Physical-Reward Policy Optimization for Accelerator RTL

This repository is the reviewer-facing artifact for the manuscript
**Physical-Reward Policy Optimization for Accelerator RTL** by Mohamed Amine
Hallam, Kuo-Kun Tseng, and Wenjie Pei, School of Computer Science and
Technology, Harbin Institute of Technology.

The repository contains the submitted manuscript sources, the supplementary
material, and a self-contained package that reproduces the completed RF versus
SFT comparison from every archived draw. The package also reruns the shared
functional simulation gate on the two RTL implementations used in the worked
FIR example.

## Start here

The [main manuscript](paper/manuscript.pdf) and
[supplementary material](paper/supplement.pdf) are available directly. Their
[LaTeX source package](paper/source-package/) includes generated claim ledgers
and file hashes.

To reproduce the supplementary comparison:

```text
python -m venv .venv
```

On Windows:

```text
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python verify_repository.py
```

On Linux or macOS:

```text
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python verify_repository.py
```

Add `--simulate` to the final command to run both archived RTL modules with
Icarus Verilog. The optional simulation requires `iverilog` and `vvp` on
`PATH`. Numerical replay does not require a GPU, Vivado, network access, or
model download.

Expected policy-level results are:

| Policy | Failure-aware utility | Functional passes |
|---|---:|---:|
| SFT | 34.24556213 MHz | 538 / 960 |
| RF | 81.95118340 MHz | 449 / 960 |

The paired RF-minus-SFT difference is 47.70562127 MHz, with a
checkpoint-conditional 95% design-bootstrap interval of
[29.99689882, 64.12540343] MHz. Functional and physical failures remain in the
denominator and receive zero utility.

## Repository layout

| Path | Contents |
|---|---|
| [`paper/`](paper/) | Main PDF, supplement PDF, and compilation sources |
| [`artifact/`](artifact/) | All 1,920 included draws, 192 physical terminal records, executable analysis, RTL demo, and provenance |
| [`checks/`](checks/) | Retained manuscript and artifact validation records |
| [`docs/`](docs/) | Submission and scope notes |
| [`REPRODUCIBILITY.md`](REPRODUCIBILITY.md) | Evidence levels, environment, commands, and limits |

## Scope

The runnable artifact provides archived-output reproduction and fresh
functional simulation of the worked RTL pair. It does not retrain the language
models or rerun Vivado. The physical endpoint is a bounded routed setup-period
search rather than full timing signoff. The new comparison is post-primary,
uses previously studied designs, and conditions its interval on the evaluated
checkpoints and draws. These limits are stated in the manuscript supplement
and in the artifact README.

No open-source license has been assigned to this repository. The material is
provided for peer review and research verification; contact the authors about
reuse or redistribution.

## Contact

- Mohamed Amine Hallam: 25sf51027@stu.hit.edu.cn
- Kuo-Kun Tseng: ykktseng@hit.edu.cn
- Wenjie Pei: wenjiecoder@outlook.com
