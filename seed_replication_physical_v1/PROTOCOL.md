# Additional-seed physical endpoint V1

Frozen after the endpoint-generation outputs for RF seeds 3/4 and correctness
seed 2 independently reached COMPLETE, and before any candidate in this package
was physically measured. This is a prospective post-primary extension; it does
not replace or pool into the original Study-2 primary interval.

The population is all 112 emitted oracle-passing SFT candidates plus all 190
emitted oracle-passing candidates from the three completed additional policies.
All incorrect/extraction/oracle-failed draws remain implicit zeros through the
20-design denominators in each generation summary. Distinct-candidate
multiplicity is retained. A physically failed emitted candidate scores zero.

Every candidate uses the validated Vivado 2026.1 V7 environment, part
`xc7z020clg400-1`, out-of-context mode, constraint-before-synthesis flow, clean
process/work/temp directory per period, constraint/path/route checks, and the
frozen V1 period search: 1--200 ns bounds, 1.5 expansion, at most four
expansions per side, 1% relative bracket tolerance, ten bisections, and fresh
boundary confirmation. A fresh validated 5-ns trial derives the search center
`D0 = 5 - WNS`; this is an initialization only, not the reported endpoint. The
reported candidate frequency is conservative `1000 / P_pass`.

An invalid 5-ns reference is repeated once. A repeated invalid reference, any
permanent invalid search measurement, missing setup path, unconstrained timing,
unclean route, nonmonotonic search, or unconfirmed boundary produces a retained
FAILED result and zero frequency. No candidate is omitted, repaired, selected,
or retried based on its frequency. Completed artifacts are hash-checked before
resume. Stop on dependency drift.

After all candidates finish, compute each policy/design endpoint as the sum of
`multiplicity * closure_frequency / original_draw_budget`, including designs
with zero emitted candidates. Report SFT and each training seed separately,
seed dispersion, and post-primary paired-design contrasts. Do not inspect
partial aggregate results to alter the protocol. Correctness seed 3 will require
a separately frozen package after its training and endpoint evaluation pass;
it is not silently appended here.
