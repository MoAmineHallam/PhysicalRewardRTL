# Completed timing-coverage audit — 2026-09-06

All 202 original SFT/RF candidate completion identities and retained artifact hashes verified.

| Arm | Candidates | Setup path | No setup path | Inconclusive | Constraint counts not confirmed clear |
|---|---:|---:|---:|---:|---:|
| sft | 112 | 108 | 1 | 3 | 3 |
| rf_s1 | 39 | 38 | 0 | 1 | 1 |
| rf_s2 | 51 | 51 | 0 | 0 | 0 |

All 197 setup-path-present candidates have zero counts for the six named constraint-coverage checks. The columns not confirmed clear are exactly the four inconclusive implementation failures, for which no routed timing report exists.

- Confirmed no-path candidate: `sft__med21__g3`.
- Inconclusive under Vivado 2026.1 after two fresh attempts: `sft__fir30_v5_8b__g2`, `sft__med19__g7`, `sft__med21__g9`, `rf_s1__iir24_v2__g1`.
- Multi-driver synthesis warnings: `sft__med21__g3`, `sft__poly12_v15_8b__g0` (warnings alone were not silently converted to failures).

## Cross-version frequency sensitivity

Diagnostic means keep every original draw in the denominator and assign zero to verified missing-path replays. Inconclusive cases make an arm mean unavailable, not zero. Original results are unchanged.

| Arm | Original mean MHz | Replay diagnostic mean MHz | Median / max symmetric error on common valid candidates (%) |
|---|---:|---:|---:|
| sft | 35.375151 | unavailable | 0.358 / 6.277 |
| rf_s1 | 84.891264 | unavailable | 0.697 / 6.277 |
| rf_s2 | 101.135428 | 100.671131 | 0.612 / 6.277 |

## Limits

This holds RTL, part, clock request and constraint order fixed but changes Vivado version. It is not period-bracketed setup closure, full hold/pulse-width sign-off, synthesized-equivalence verification, or a corrected primary confidence interval. A setup path alone is insufficient: the named constraint checks are reported separately. Multi-driver warnings are recorded in analysis.json and require review; they are not silently converted into physical failures.
