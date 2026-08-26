# Correctness-Gated Policy Optimization for High-Frequency DSP Accelerator RTL

Research code, RTL, evaluation artifacts, and manuscript sources for studying
whether correctness-gated policy optimization can shift an RTL generator toward
faster implementations under real FPGA measurements.

The learned timing model is used only as a training reward. Reported hardware
performance comes from Vivado post-route measurements, and the primary endpoint
penalizes incorrect or implementation-failed samples with zero frequency.

## Project status

- The completed sealed Study 2 covers 20 unseen designs, two independent RF
  training seeds, matched MLP and correctness controls, and 489 Vivado PPA rows.
  Its frozen outcome is `full_two_regime_repair`.
- The earlier 30-design, five-family result is retained as supporting evidence;
  it is not pooled with or substituted for sealed Study 2.
- A new provenance-bound Study 2 PYNQ-Z2 sweep covers five paired designs. It
  shows two RF wins, two ties, and one loss with zero Fmax spread across three
  runs. Because correctness eligibility was added after an explicitly recorded
  infeasible first selection, this is descriptive support rather than an
  independent confirmatory result. The historical asymmetric comparison stays
  excluded.

For timestamped experimental history and negative results, see
[`MASTER_REFERENCE.md`](MASTER_REFERENCE.md). For the paper-specific
reproducibility contract, see [`paper/README.md`](paper/README.md).

## What is in this repository

| Path | Contents |
|---|---|
| `paper/` | IEEE TCAD manuscript, generated tables, figures, and claim ledger |
| `rtl/` | Generated evaluation candidates, manifests, and committed PPA rows |
| `rtl_library/` | Parameterized RTL catalogue, specifications, and golden models |
| `analyze_main_results.py` | Generator for the earlier 30-design supporting analysis |
| `analyze_study2_secondary.py` | Fail-closed generator for sealed Study 2 comparison and conditional-PPA tables |
| `analyze_study2_board.py` | Raw-trace and provenance verifier plus generator for the Study 2 silicon table |
| `verify_claims.py` | Fails closed on stale artifacts, unresolved pointers, or untracked prose numbers |
| `oracle.py` | Icarus-based functional equivalence oracle |
| `canonicalize.py` | Lexical canonicalizer and mutation/trace contract |
| `preregistration.json` | Original sealed-study declaration and amendments |
| `preregistration_study2.json` | Separate reward-eligible Study 2 declaration |
| `hashes.json`, `hashes_study2.json` | Reproducible artifact identity manifests |

The repository retains failures, withdrawals, and exploratory artifacts rather
than silently replacing them. Evidence tiers in `paper/README.md` distinguish
primary comparisons, replications, controls, diagnostics, and context.

## Reproduce the paper artifacts

From the repository root, run:

```powershell
python gen_study2_board.py --check
python analyze_main_results.py
python analyze_study2_secondary.py
python analyze_study2_board.py
python verify_claims.py
python -m unittest -v test_sealed_workflow.py
```

The first command validates the paired Study 2 board inputs. The analysis
commands regenerate the supporting 30-design outputs, sealed Study 2 tables,
and descriptive silicon table. `verify_claims.py` checks all three ledgers and
every manuscript number against artifact source pointers. The unit tests exercise the sealed
workflow contracts without requiring a GPU.

Generated paper artifacts are written under `paper/generated/`. In particular:

- `claims.json` records values, methods, and source line ranges;
- `claim_provenance.md` is the human-readable provenance ledger;
- `main_results.json` contains the complete primary and secondary audit object;
- `study2_claims.json` and `study2_secondary_results.json` contain the sealed
  Study 2 closure and its bounded post-primary comparisons;
- `study2_board_claims.json` and `study2_board_results.json` contain the
  provenance-checked, explicitly descriptive live-silicon summary;
- `table_*.tex` and verified figures are regenerated rather than hand-copied.

## Environment

The frozen Study 2 environment uses Python 3.10, PyTorch 2.4.1 with CUDA 12.1,
Transformers 4.46.3, PEFT 0.13.2, NumPy 2.2.6, SciPy 1.15.3,
scikit-learn 1.7.2, and Icarus Verilog 12.0. Real PPA evaluation uses Vivado
2023.1 targeting `xc7z020clg400-1`; the optional silicon target is a PYNQ-Z2.

Large base-model and adapter directories are intentionally not committed.
Their complete directory-manifest digests are pinned in the hash manifests.
GPU training or sealed generation therefore requires separately obtained model
weights and checkpoints with matching identities. The artifact-only analysis,
claim verification, and most regression tests operate from committed files.

## Compile the manuscript

With a TeX installation available:

```powershell
Set-Location paper
pdflatex main
bibtex main
pdflatex main
pdflatex main
```

The manuscript is a work in progress. Recheck the current venue rules and have
every qualifying author review the paper and its generative-AI disclosure before
submission.

## Important limitations

- Held-out designs are unseen parameterizations from the same generator
  families, not evidence of unrestricted cross-template generalization.
- WNS-derived frequency comes from a fixed implementation flow and is not a
  universal timing-closure guarantee.
- Learned-reward values are diagnostics, never hardware results.
- A generated bitstream is not a silicon measurement.
- Partial or exploratory runs must not be promoted to confirmatory evidence.

## License and citation

No open-source license has been selected yet. Public availability does not by
itself grant permission to reuse the code or data. Citation metadata will be
added with the finalized manuscript; until then, please cite the repository and
the manuscript title above.
