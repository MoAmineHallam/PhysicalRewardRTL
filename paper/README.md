# TCAD paper reproducibility contract

This is the TCAD-first integrated capability paper. The strongest headline
evidence is the separately frozen 20-design sealed Study 2; the earlier
30-design, five-family `grpo_v8` evaluation remains supporting evidence and is
never silently pooled with the sealed result. The manuscript migration to this
ordering must retain the explicit evidence labels in both generated ledgers.

## Regenerate and verify

From the repository root:

```powershell
python gen_symmetric_holdout_bitstream.py --check
python analyze_main_results.py
python analyze_study2_secondary.py
python verify_claims.py
```

Keep this order. The symmetric-board preflight refreshes its selection manifest;
the two artifact generators rebuild the earlier supporting analysis and sealed
Study 2 closure, and the verifier finally checks both ledgers.

`analyze_main_results.py` is the sole generator for empirical manuscript
values and verified figures for the earlier 30-design analysis. It fails closed if that
evaluation is not exactly 30 designs (19 interpolation, 11 extrapolation), if
either policy lacks its 48-sample denominator, or if a manifest candidate lacks
a PPA row. The primary endpoint is mean per-design equal-sample post-route
Fmax: incorrect and implementation-failed samples score zero.

`analyze_study2_secondary.py` is the sole generator for the sealed Study 2
direct RF--MLP table, conditional resource/power table, and their separate
claim ledger. It first verifies the immutable sealed outcome, all 489 PPA rows,
the frozen resample-plan hashes, and the post-primary secondary-analysis
specification. The preregistered RF--SFT result remains the primary endpoint;
direct RF--MLP and resource/power comparisons are bounded secondary evidence.

The same script independently validates each secondary artifact before adding
claims:

- raw-model correctness over the complete primary design universe;
- the 22-design, three-family Qwen-Coder replication;
- candidate multiplicities and concentration statistics;
- the two-arm, same-task API baseline;
- the committed VerilogEval per-sample verdicts;
- `rtl/hls_baseline/hls_results.json`, including a cross-check of every selected
  GRPO value against the committed held-out Vivado rows; and
- the bounded lexical/reflow diagnostic in `reflow_attribution.json`.

Generated files live under `paper/generated/`:

- `claims.json`: values, methods, and artifact `file:line` ranges;
- `claims.tex`: named `\claim{...}` definitions;
- `claim_provenance.md`: human-readable claim ledger;
- `main_results.json`: primary and secondary audit object; and
- `table_*.tex`: generated manuscript tables.
- `study2_claims.json`, `study2_claims.tex`, and
  `study2_claim_provenance.md`: the sealed Study 2 ledger; and
- `study2_table_comparison.tex` and `study2_table_ppa.tex`: generated Study 2
  comparison and conditional-PPA tables.

Verified figures are `fig_main_verified`, `fig_mechanism_verified`, and
`fig_trajectory_verified` in PDF and PNG form.

`verify_claims.py` recomputes the generated outputs, validates every source
pointer, recursively resolves TeX inputs, rejects unknown claim identifiers,
and fails on raw numeric literals in authored manuscript prose. If a value is
not in the generated ledger, it does not enter the paper.

## Evidence tiers

The manuscript labels evidence by what it can support:

- **Primary causal comparison:** frozen 20-design sealed Study 2 SFT-versus-RF
  evaluation, equal sample cost, two independent RF seeds, real post-route
  measurements, and incorrect/failed samples scored at zero.
- **Supporting comparison:** the earlier 30-design RTLCoder SFT-versus-GRPO
  result, kept separate from Study 2.
- **Bounded secondary evidence:** direct RF-versus-MLP paired intervals and
  conditional resource/power trade-offs on fixed common support.
- **Replication:** Qwen-Coder repeats the complete SFT-to-GRPO pipeline on the
  earlier 22-design scope.
- **Mechanism:** candidate-level real-Fmax distributions and multiplicities.
- **Context:** the API prompt arms and selected-candidate HLS comparison. These
  are not pooled with the primary endpoint.
- **Control:** VerilogEval separates SFT specialization cost from additional
  GRPO regression.
- **Diagnostic:** the trajectory/reflow analysis documents one late proxy
  failure without claiming a general reward repair.

The small-student study remains exploratory because it has no complete
held-out PPA evaluation. The historical board comparison remains excluded
because its SFT and GRPO selection rules were asymmetric.

## Silicon rule

Only `rtl/holdout_silicon_symmetric/catalog_fmax.json`, produced by a live sweep
after symmetric candidate selection, may create a silicon table. A generated
bitstream is not a measurement. Until that file exists and its hashes validate,
the generated paper states that no symmetric silicon result is available.

## Compile

```powershell
Set-Location paper
pdflatex main
bibtex main
pdflatex main
pdflatex main
```

The current Windows environment does not expose a TeX compiler on `PATH`; use a
TeX installation or import the repository into Overleaf with `paper/main.tex`
as the main document.

## TCAD submission contract

The manuscript uses `\documentclass[journal]{IEEEtran}` and the IEEE two-column
journal layout. Current TCAD instructions allow at most 14 submission pages for
a regular paper. The accepted-paper charging policy currently permits 9 pages
before mandatory overlength charges; these rules must be rechecked on the live
TCAD author page immediately before submission.

TCAD requires a generative-AI disclosure and lists omission as a desk-rejection
ground. `sections/08_acknowledgment.tex` discloses Codex assistance with code
auditing, analysis development, LaTeX drafting, and editing. Do not delete or
weaken that statement. Every qualifying author must review and approve it.

TCAD does not allow concurrent submission. Before upload, the corresponding
author and supervisor must reconcile every prior review or public version and
complete the disclosure portion of `TCAD_SUBMISSION.md`. Do not assert that
there was no earlier submission unless all authors confirm it.
