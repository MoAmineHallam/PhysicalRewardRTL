# TCAD submission checklist and cover-letter draft

This file tracks submission-only facts that cannot be inferred safely from the
repository. It is not part of the compiled manuscript and is not a substitute
for checking the live TCAD instructions.

## Blocking checklist

- [ ] Supervisor has reviewed the scientific framing and decided the complete
  author list and order.
- [ ] Every author has an ORCID and has approved the final manuscript.
- [ ] Prior conference, journal, workshop, and preprint history has been listed
  honestly in the cover letter.
- [ ] No version of this work is concurrently under review.
- [x] The 2026-09-05 working PDF compiles to 14 pages, within the regular-paper
  submission limit. Font substitution and underfull-box warnings remain;
  recheck the final submission build after any further edits.
- [x] All citations, figure fonts, equations, tables, and cross-references have
  been inspected in the rendered PDF.
- [x] `python analyze_main_results.py --check`,
  `python analyze_study2_secondary.py --check`,
  `python analyze_study2_board.py --check`,
  `python paper/make_revision_evidence.py --check`,
  `python paper/make_verified_figures.py --check`, and
  `python verify_claims.py` pass from the repository root.
- [ ] The generative-AI acknowledgment remains complete and accurate.
- [ ] The public artifact URL resolves at the exact submitted commit.
- [ ] The corresponding author has selected Traditional or Open Access
  publication with the institution's funding rules understood.

## Scientific checks before calling the manuscript final

The exact 2026-09-05 PDF is an archived working draft, not a compliance-certified
submission. The detailed completed/remaining handoff is at the top of
`MASTER_REFERENCE.md`.

- [ ] Finish the running 302-candidate additional-seed physical evaluation if it
  is to enter this submission. RF3/RF4/correctness2 endpoint generation and
  output audits are complete; correctness3 training remains one update short at
  the last check. Keep the extension separate from the original primary result.
- [x] Audited all 202 original SFT/RF candidates for timing-path coverage under
  Vivado 2026.1. One SFT missing-path/default-frequency artifact was confirmed;
  four cross-version implementation failures remain inconclusive. See
  `timing_coverage_extension_v1/REPORT.md`. This does not establish hold or
  pulse-width closure and is not silently substituted for the frozen endpoint.
- [ ] Decide with the supervisor whether the sampled 0.999-threshold oracle
  needs stronger exact-equivalence evidence for the proposed claim scope.
- [ ] Decide whether to add a matched contemporary external optimizer baseline.
  The current paper explicitly does not establish superiority to those systems.
- [ ] Review the package-level RF/MLP comparison, shared-SFT seed scope,
  matched VerilogEval regression, and amended board-selection limitations.

## Formatting and editorial cleanup still required

- [x] Added numbered prose callouts for Tables II and IX and fixed first-callout
  order in the editorial follow-up, `build/revision-2026-09-05-editorial/main.pdf`.
- [x] Alphabetized index terms and consistently used `Fig.` in prose.
- [ ] Finish acronym definitions and remove terminal periods from table captions.
- [ ] Complete and verify bibliography metadata and publication versions.
- [ ] Review small figure labels against the differing current general IEEE
  and older linked TCAD production guidance; preserve readability.
- [ ] Rebuild after cleanup and new evidence; recheck font warnings, grayscale
  legibility, table styling, and the 14-page limit.
- [ ] Prepare the self-contained submission package and any production-stage
  figure naming, caption lists, biographies, and photos requested by the portal.

## Optional evidence that could strengthen a later revision

The manuscript already includes two independent primary RF seeds, the frozen
paired interval, matched MLP/correctness controls, and a symmetric live PYNQ-Z2
sweep. A second FPGA family or a larger independently selected board sample
would strengthen external validity, but is not silently treated as part of the
present evidence. It may be added only under a prospectively frozen protocol
and after passing the canonical verifier.

## Cover-letter draft

Dear Editor-in-Chief,

Please consider the manuscript "Correctness-Gated Policy Optimization for
Streaming-Accelerator RTL: A Failure-Aware Post-Route Study" for publication as a Regular Paper in the
IEEE Transactions on Computer-Aided Design of Integrated Circuits and Systems.

The manuscript studies whether correctness-gated policy optimization improves
the fixed-cost physical-utility distribution of generated RTL, rather than only
the best candidate returned by EDA-guided selection. Its primary evaluation
preserves sample multiplicity, assigns zero physical performance to incorrect
and implementation-failed draws, and reports only real post-route EDA
measurements. Matched physical-reward and correctness-only controls test
whether functional-yield changes explain the gain; RF versus MLP remains a
reward-package comparison, not an isolated predictor ablation. A second code-model
backbone, candidate-distribution analysis, contextual baselines, and a measured
proxy-overoptimization trajectory test the scope and mechanism of the result.

The work fits TCAD because it contributes an automated RTL-generation and
evaluation method centered on functional verification, synthesis, physical
design, and performance optimization. The repository provides the frozen raw
artifacts, fail-closed result and figure generators, and claim ledgers
connecting manuscript values to artifact line ranges.

[REQUIRED BEFORE SUBMISSION: disclose every related version reviewed or
published during the period required by TCAD. If none exists, state that only
after all authors confirm it. Explain substantive differences from any prior
version.]

[REQUIRED BEFORE SUBMISSION: identify any conflicts with TCAD Associate
Editors, or state that the authors are unaware of any conflicts after checking
the current editorial board.]

The manuscript includes the required acknowledgment describing the use of
OpenAI Codex in repository auditing, analysis-code development and review,
literature discovery and metadata checking, LaTeX scaffolding, and drafting and
editing throughout the manuscript. Codex was not treated as a source. All
authors must review the generated material and accept responsibility for the
submitted work before this letter is finalized.

[CONFIRM BEFORE SUBMISSION: This manuscript is not concurrently submitted
elsewhere. All authors have approved the manuscript and its submission to TCAD.]

Sincerely,

[Corresponding author name, affiliation, ORCID, and contact details]
