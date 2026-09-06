# Confirmed cross-version missing-path artifact — 2026-09-05

The instrumented Vivado 2026.1 replay of the original
`rtl/sealed_sft/sft__med21__g3.sv` reproduces the suspicious record exactly:
one clock, **zero setup paths**, zero LUT/FF/DSP/BRAM resources, zero default
slack, and a historical-formula frequency of 200 MHz. That number is not a
measured timing capability of this replayed implementation.

The retained synthesis log reports multi-driven `y` nets, with a constant
driver preserved and the other driver ignored (`Synth 8-6858/8-6859`).
The routed functional netlist connects all sixteen output bits to GND. This
confirms the constant-collapse mechanism in the replay and illustrates why an
RTL simulation pass is not proof of synthesized functional equivalence.

Evidence in `replay_20260905_02/`:

- `reports/path_diagnostic.json`: clock/path counts and historical arithmetic.
- `stdout.log`: synthesis warnings and complete implementation output.
- `reports/routed.v`, `reports/routed.dcp`: constant-zero netlist/checkpoint.
- `reports/check_timing.txt`, `timing_summary.txt`, `route_status.txt`,
  `clocks.txt`, `utilization.txt`, and `constraints.xdc`.
- `launch.json` and `completion.json`: exact command, input hashes and passing
  V7 dependency guards before and after execution. All report exports succeeded.

The first attempt (`replay_20260905/`) failed at Vivado startup under the sandbox
with file-access/Tcl-app errors. It is retained as an infrastructure failure,
not scored as a candidate failure. The second attempt used a fresh short
scratch directory `C:\TPA0905` and approved unsandboxed execution.

## Interpretation and correction boundary

The original record came from Vivado 2023.1. No historical routed checkpoint or
path report survives, so this is **not an exact historical reproduction**.
The replay establishes the artifact under 2026.1, matching the original
zero-resource/zero-slack fingerprint. Do not silently overwrite original data.

The already computed diagnostic sensitivity sets this one SFT sample's physical
score to zero while preserving its multiplicity (one of 48 med21 draws). It
changes SFT's overall mean from 35.375151 to 35.166817 MHz and RF-minus-SFT from
57.638196 to 57.846529 MHz. Thus this specific artifact does not explain the
RF improvement; it slightly favors the SFT baseline. No corrected confidence
interval or manuscript-wide correction is asserted here.

The broader, frozen `timing_coverage_extension_v1` now replays all 202 original
SFT/RF candidates with the same diagnostics. Its coverage, error distribution,
and any further invalid cases must be reviewed before a documented correction
or sensitivity analysis is integrated. This audit does not establish full
timing sign-off or formal functional correctness.
