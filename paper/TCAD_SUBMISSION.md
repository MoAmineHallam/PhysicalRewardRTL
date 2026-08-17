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
- [ ] The IEEE journal PDF compiles cleanly and is within the current TCAD
  submission page limit.
- [ ] All citations, figure fonts, equations, tables, and cross-references have
  been inspected in the rendered PDF.
- [ ] `python gen_symmetric_holdout_bitstream.py --check`,
  `python analyze_main_results.py`, and `python verify_claims.py` pass from the
  repository root.
- [ ] The generative-AI acknowledgment remains complete and accurate.
- [ ] The public artifact URL resolves at the exact submitted commit.
- [ ] The corresponding author has selected Traditional or Open Access
  publication with the institution's funding rules understood.

## Evidence still worth adding before submission

Highest value: independent primary training seeds on the same frozen split.
Next: a successful symmetric bitstream and live board sweep, or an additional
FPGA target using the identical policy samples. Neither may be described as
complete until its artifact passes the canonical verifier.

## Cover-letter draft

Dear Editor-in-Chief,

Please consider the manuscript "Correctness-Gated Policy Optimization for
High-Frequency DSP Accelerator RTL" for publication as a Regular Paper in the
IEEE Transactions on Computer-Aided Design of Integrated Circuits and Systems.

The manuscript studies whether correctness-gated policy optimization changes
the one-draw physical-quality distribution of generated RTL. Its primary
evaluation keeps sampling cost fixed, assigns zero physical performance to
incorrect and implementation-failed samples, and reports only real post-route
EDA measurements. A second code-model backbone, candidate-distribution
analysis, contextual baselines, and a measured proxy-overoptimization
trajectory test the scope and mechanism of the result.

The work fits TCAD because it contributes an automated RTL-generation and
evaluation method centered on functional verification, synthesis, physical
design, and performance optimization. The repository provides the frozen raw
artifacts, a single fail-closed result generator, and a claim ledger connecting
manuscript values to artifact line ranges.

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
authors have reviewed the generated material and accept responsibility for the
submitted work.

This manuscript is not concurrently submitted elsewhere. All authors have
approved the manuscript and its submission to TCAD.

Sincerely,

[Corresponding author name, affiliation, ORCID, and contact details]
