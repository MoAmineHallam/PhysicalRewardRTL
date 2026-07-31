# paper/

LaTeX source for the paper, in Elsevier `elsarticle` format.

## Layout

```
main.tex            preamble, front matter, \input of sections
sections/*.tex      01 intro, 02 related, 03 method, 04 setup,
                    05 results, 06 discussion, 07 conclusion
refs.bib            bibliography (entries marked VERIFIED were checked
                    against a live arXiv/publisher record)
make_figures.py     regenerates every figure from measurement artifacts
figures/*.pdf       generated — do not edit by hand
```

## Regenerating the figures

Every figure is derived from the committed `ppa.jsonl` / manifest / summary
files, so a figure can never disagree with the results tables. Run wherever
those artifacts exist (the laptop is convenient — it produced them):

```bash
python paper/make_figures.py            # all figures -> paper/figures/
python paper/make_figures.py --only money,mechanism
python paper/make_figures.py --png      # also PNG previews for quick viewing
```

Requires `numpy` and `matplotlib` only. Each figure prints the values it
plotted so they can be cross-checked against `RESULTS.md` by eye.

Then commit:
```bash
git add paper/figures && git commit -m "paper figures" && git push
```

| figure | source data |
|---|---|
| `fig_pipeline` | schematic (no data) |
| `fig_money` | `rtl/holdout_eval_v8_{firfirr,poly,iirmed}/` |
| `fig_mechanism` | same (per-candidate) |
| `fig_bestofn` | `rtl/holdout_eval/bestofn.json` |
| `fig_saturation` | `holdout_summary.json` × 3 chunks |
| `fig_silicon` | `rtl/holdout_silicon/catalog_fmax.json` |
| `fig_distill` | probe literals (see docstring) |
| `fig_area` | `rtl/holdout_eval/bestofn.json` (area block) |

`fig_money`, `fig_mechanism` and `fig_saturation` need the grpo_v8 `ppa.jsonl`
files; they skip with a message until those are pulled.

## Compiling

```bash
cd paper && pdflatex main && bibtex main && pdflatex main && pdflatex main
```

Or import the repo into Overleaf (New Project → Import from GitHub) and set
`paper/main.tex` as the main document.

## Rules

- **Never type a measured number into a `.tex` file by hand.** Take it from
  `RESULTS.md`, which is derived from the artifacts.
- **No surrogate-derived frequency is ever reported.** Every \fmax in the paper
  is timing-closed Vivado or a measured hardware sweep (invariant #2).
- Numbers currently in the tables correspond to `RESULTS.md` as of the
  5-family Vivado pass; re-check §2a, §7, §7b, §2c, §5, §8b after any re-run.
