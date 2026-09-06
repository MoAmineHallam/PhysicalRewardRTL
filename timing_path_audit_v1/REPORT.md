# Read-only Study-2 timing audit — 2026-09-05

## Outcome

Audited 489 frozen candidate rows: 488 compiled and 1 explicit implementation failure. The primary SFT/RF comparison contains 202 candidate rows.

Frozen measurement-script, runner, manifest, PPA, and emitted-RTL hashes were checked. All four endpoint-arm means were independently reconstructed without changing any outcome.

| Directory | Candidates | Compiled | Zero-slack suspects |
|---|---:|---:|---:|
| sealed_sft | 112 | 112 | 1 |
| sealed_rf_s1 | 39 | 39 | 0 |
| sealed_rf_s2 | 51 | 51 | 0 |
| sealed_rf_mid_s1 | 24 | 24 | 0 |
| sealed_rf_mid_s2 | 29 | 29 | 0 |
| sealed_mlp_s1 | 103 | 102 | 0 |
| sealed_mlp_s2 | 64 | 64 | 0 |
| sealed_corr_s1 | 67 | 67 | 0 |

## Suspect and exact scope of inference

The frozen Tcl initializes slack to zero and replaces it only when a setup path returns numeric slack. An unchanged default therefore yields 200 MHz at the frozen 5 ns request. Its comment claiming a missing path scores zero frequency contradicts the executed formula.

- `sft__med21__g3` (rtl/sealed_sft/ppa.jsonl:85): 1/48 draws for med21; recorded slack 0.0 ns and frequency 200.0 MHz; zero LUT/FF/DSP/BRAM counts: True.

The suspect's RTL assigns `y` in both combinational and clocked processes. This is a plausible synthesis/simulation mismatch mechanism, not a confirmed diagnosis without the original netlist or an instrumented replay.

Every other compiled row has nonzero finite slack and consistent frequency arithmetic. Thus none can have been scored by the unchanged zero-default branch, assuming the hash-bound script and retained row are the measurement authority. This does not certify clock coverage, complete routing, hold/pulse timing, or synthesized functionality.

## Diagnostic sensitivity only

Set the suspect's physical score to zero while retaining its draw in the denominator. This is not yet a correction to the manuscript or its original confidence interval.

| Quantity | Frozen result (MHz) | Zero-suspect scenario (MHz) |
|---|---:|---:|
| SFT overall | 35.375151 | 35.166817 |
| RF overall | 93.013346 | 93.013346 |
| RF minus SFT overall | 57.638196 | 57.846529 |
| RF minus SFT median-family mean | -3.355268 | -1.271934 |

## What remains

- No original per-candidate timing/constraint reports or checkpoints were retained in the eight sealed directories. The aggregate launcher log cannot establish path coverage.
- First replay only the flagged SFT candidate with diagnostics that retain synthesis warnings, resource counts, clocks, setup-path count, constraints, routed netlist/checkpoint, and timing reports. Preserve the original RTL, part, 5 ns request, and constraint order.
- Vivado 2023.1 is installed but the repository records later runtime instability on this Windows host. A 2026.1 replay must be labeled cross-version diagnostic, not an exact reproduction or retroactive replacement of a 2023.1 observation.
- Freeze any broader coverage/closure diagnostic before launching it; include both arms and preserve failure/multiplicity accounting. Do not silently rerun only favorable cases.
- If an invalid physical score is confirmed, publish an explicit correction and propagate it through affected analyses. Preserve the original version as historical evidence.

No GPU jobs, Vivado processes, original results, manuscript files, or GitHub state were changed.

Reproduce with `python timing_path_audit_v1/audit.py --check`. JSON includes per-candidate findings and LF-normalized source hashes.
