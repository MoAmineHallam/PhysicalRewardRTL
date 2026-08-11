# Focused preprint — Overleaf instructions

1. Zip this folder and upload to Overleaf (New Project → Upload Project).
2. Set **main.tex** as the root document; compiler **pdfLaTeX**.
3. It compiles as-is. Figures are switched OFF (`\figuresfalse` near the top of
   main.tex) because Figure 1 needs Vivado results that may not exist yet.

## Adding Figure 1

Figure 1 is the hero: predicted vs measured Fmax along the optimisation path.
It needs `rtl/traj_v8/ppa.jsonl` and `rtl/traj_v9/ppa.jsonl`. Once the laptop
has produced them:

    python make_figs.py          # writes figures/fig1_trajectory.pdf

then change `\figuresfalse` to `\figurestrue` in main.tex and re-upload
`figures/`. If the results are missing the script says exactly which and writes
nothing, so a half-built figure cannot reach the document.

## Every number is traceable

| table | regenerate with |
|---|---|
| Table I  (predictor error)        | `python analyze_surrogate_error.py` |
| Table II (trajectory)             | `rtl/traj_v8/holdout_summary.json` |
| Table III (ablation)              | `python analyze_policy_fmax.py --dirs rtl/holdout_eval_ablate_const` |
| Table IV (repair)                 | `python analyze_surrogate_error.py --pred pred_v4.jsonl` |
| Table V  (re-optimisation)        | `python analyze_policy_fmax.py --dirs rtl/holdout_eval_v9` |
| §Evaluation integrity             | `python audit_oracle.py --report` |

## Known gaps before posting

- Figure 1's measured line (Vivado running).
- The oracle drops non-numeric simulation output on 18 of 1,529 candidates;
  §Evaluation integrity should not be published until that is rejected properly
  and the audit re-run.
- The leave-one-design-out comparison in Table IV is on different pair sets;
  it is flagged as an observation in a footnote, not a controlled result.
