# Figure redesign and layout check — 2026-09-05

## Reference basis

The four complete PDFs supplied by the author are preserved in
`references/style/`. The comparisons below concern their actual supplied
versions, not a claim that every arXiv version is a TCAD typeset article.

| Reference | Inspected visual example | Applied design lesson |
|---|---|---|
| [RTLCoder](https://arxiv.org/pdf/2312.08617), local v5 | Page 3: staged framework with pass/fail loops | Explicit stages, named gates, feedback routing, full-width placement |
| [ChatEDA](https://arxiv.org/pdf/2308.10204), local v4 | Page 4: detailed task/script framework | Concrete implementation content inside grouped panels |
| [CodeV](https://arxiv.org/pdf/2407.10424), local v5 | Page 2: four-column pipeline with strong headers | Aligned columns, restrained backgrounds, clear panel hierarchy |
| [Understanding and Mitigating Errors](https://arxiv.org/pdf/2508.05266), local v2 | Pages 9 and 11: verification modules and full-width framework | Distinguish data/control paths and separate architecture from quantitative outcomes |

[IEEE graphics sizing guidance](https://journals.ieeeauthorcenter.ieee.org/create-your-ieee-journal-article/create-graphics-for-your-article/resolution-and-size/)
supports vector PDF and widths of approximately 3.5 inches (one column) and
7.16 inches (two columns). [IEEE graphics preparation guidance](https://conferences.ieeeauthorcenter.ieee.org/write-your-paper/improve-your-graphics/)
recommends consistent fonts and approximately 9–10 pt labels at final size.
The present diagrams use mostly 8–8.7 pt labels, with compact 7.3 pt repeated
family labels in the board bank: these were inspected at placed size, but this
is a readability compromise, not a claim to meet a hard 9 pt minimum.
[TCAD submission instructions](https://ieee-ceda.org/publications/tcad/tcad-paper-submissions)
set the regular-paper submission limit at 14 pages; the body remains the
standard 10 pt IEEEtran journal layout.

## Implemented design

Both schematics are code-native vector drawings, not raster illustrations.
Source: `diagram_art.py`, invoked by `make_verified_figures.py`. PDF is embedded
in LaTeX; SVG is retained for editing and PNG for preview. All output hashes
and source dependencies are recorded in `generated/figure_manifest.json`.
Text-input and SVG hashes normalize CRLF to LF for Git checkout portability;
PDF and PNG hashes remain byte-exact. Exact regeneration also requires the
recorded plotting environment and the same installed fonts.

The training schematic contains four technical stages: frozen resources,
policy learning, gated reward packages, and held-out physical evaluation. It
shows group sampling, flat-group skips, the frozen reference, canonicalization,
structural features, log-prediction clipping and exponentiation, rejection-zero
branches, checkpoint freezing, implementation, and restored sample multiplicity.
Reward feedback is kept separate from held-out reporting.

The board schematic contains the amended selection contract, actual PS/PL test
harness, and trace-validation path. It shows the Python/MMIO clock controller,
shared stimulus, paired SFT/RF DUT bank, echo canary, selector mux, capture
buffer, clock/control paths, golden stream, and boundary extraction. Sources
include `rtl/sealed_study2_board/dut_top.v`, `rtl/la_axi_fast.v`,
`gen_study2_board.py`, and `sweep_catalog.py`. It is a logical architecture,
not a placement drawing or a complete signal-level netlist.

Rectangular modules, orthogonal routing, thin strokes, muted stage colors, and
consistent typography add information density without decorative chip artwork.
Pass/fail text and line styles supplement color. No circuit topology, measured
outcome, or validation result was invented to make either diagram denser.

## Placement in the compiled draft

After author feedback, both diagrams were compacted without changing their
7.16-inch width, font sizes, or technical content. The training canvas decreased
from 376 to 300 pt (20.2% shorter); the board canvas decreased from 307 to 270 pt
(12.1% shorter). Blocks and routes were repositioned, with tighter internal
padding and inter-stage gaps, rather than scaling the text. Both remain on
pages 2 and 7 respectively, and the rebuilt manuscript remains 14 pages.

| Printed figure | Asset stem | Placement | PDF page |
|---|---|---|---|
| 1: training/evaluation | `fig01_training_evidence_boundary_v3` | Two-column top float after introductory first mention | 2 |
| 2: board architecture | `fig04_board_architecture_v2` | Two-column top float after board-protocol first mention | 7 |
| 3: primary comparison | `fig02_study2_primary` | Two-column results float, with all 20 designs retained | 8 |
| 4: matched controls | `fig03_study2_controls` | Two-column results float | 9 |
| 5: measured board outcomes | `fig04b_board_outcomes` | One-column float beside board evidence | 10 |
| 6: reward reliability | `fig06_reward_reliability` | Two-column float after diagnostic first mention | 12 |

Captions are below figures and identify panels, denominators, uncertainty, and
scope where needed. The board architecture was moved into the experimental
protocol; its five measured pairs now have a separate compact plot. Numeric
interval text already present in tables is not repeated as crowded plot
annotations. The legacy `fig05_probability_reallocation` export is retained for
compatibility but is not included in the current manuscript.

## Validation and handoff

`build/revision-2026-09-05/main.pdf` compiles to 14 pages. All pages were visually
inspected, including figures at their actual placed scale. No overfull boxes or
unresolved references were reported. Tectonic reports font substitutions and
underfull boxes; a final Overleaf/pdfLaTeX build still needs pagination review.
The older `build/main.pdf` has not been replaced.

The following checks passed during this revision:

- `python analyze_main_results.py --check`
- `python analyze_study2_secondary.py --check`
- `python analyze_study2_board.py --check`
- `python paper/make_revision_evidence.py --check`
- `python paper/make_verified_figures.py --check` (exact output reproduction)
- `python verify_claims.py` (440 source-resolved claims; 265 used manuscript IDs)

These are artifact consistency checks, not independent scientific validation.
The optional LODO rerun was not executed. Diagram redesign does not change the
frozen primary result or establish TCAD acceptance readiness. Additional-seed
physical evaluation, timing-path auditing, oracle scope, external comparisons,
and supervisor/author approval remain explicit in `TCAD_SUBMISSION.md`.
