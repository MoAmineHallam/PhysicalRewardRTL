# Paper reproducibility contract

The manuscript is an IEEE-format recovery draft centered on the frozen
thirty-design `grpo_v8` evaluation. Empirical values are not copied from
`RESULTS.md` and must not be typed into the TeX source.

## Regenerate and verify

From the repository root:

```powershell
python analyze_main_results.py
python verify_claims.py
```

`analyze_main_results.py` is the sole generator for headline result tables. It
requires exactly the three frozen evaluation chunks and fails if they do not
contain exactly thirty designs, the expected interpolation/extrapolation split,
both policies, a common sample count, and a PPA row for every manifest
candidate. The primary endpoint is equal-sample post-route Fmax: incorrect and
implementation-failed samples score zero.

Generated files live under `paper/generated/`:

- `claims.json`: values, computations, and artifact `file:line` ranges;
- `claims.tex`: TeX definitions for named `\claim{...}` references;
- `claim_provenance.md`: human-readable claim ledger;
- `main_results.json`: design-level and aggregate audit object;
- `table_*.tex`: generated headline tables.

The canonical script also regenerates `fig_main_verified` and
`fig_trajectory_verified` in PDF and PNG form.

`verify_claims.py` independently reproduces the earlier correctness,
best-of-N, trajectory, and oracle audits. Its manuscript check additionally:

- reruns the canonical generator in stale-check mode;
- validates every claim source path and line range;
- recursively resolves the TeX inputs;
- fails on an unknown `\claim{...}` identifier; and
- fails on any raw numeric literal in authored title, abstract, or prose.

That last rule is intentional. If a result is not in the generated ledger, it
does not enter the manuscript.

## Silicon rule

The historical `rtl/holdout_silicon/catalog_fmax.json` comparison is asymmetric
(SFT median versus GRPO maximum) and is excluded from the recovery draft. Only
`rtl/holdout_silicon_symmetric/catalog_fmax.json`, produced after symmetric
median-versus-median selection and a new live sweep, may support a silicon
number. A generated bitstream is not a measurement.

## Compile

```powershell
Set-Location paper
pdflatex main
bibtex main
pdflatex main
pdflatex main
```

The local Windows environment used for this recovery did not expose a TeX
compiler on `PATH`; use a TeX installation or import the repository into
Overleaf and select `paper/main.tex` as the main document.
