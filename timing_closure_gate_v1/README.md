# Timing-closure gate v1

This directory contains a post-Study-2 validation of the manuscript's
single-request, WNS-derived frequency metric. It does **not** amend, overwrite,
or reopen sealed Study 2. The old `ppa_synth.tcl` and every existing Study 2
candidate, manifest, PPA row, and analysis artifact remain immutable inputs.

The pilot closes ten predeclared raw RTL candidates: one SFT/RF pair for one
deterministically selected design in each of the five represented families.
Candidate selection uses only already-recorded Study 2 metadata and the old
5-ns proxy; it occurs before any candidate-specific closure result exists.

## Files

- `preregistration.json` freezes the selection, search, scoring, and stop rules.
- `generate_manifest.py` deterministically selects and materializes the ten RTL
  inputs, or checks an already-frozen manifest without rewriting it.
- `manifest.json` and `manifest.sha256` are the frozen pilot identity.
- `inputs/` contains byte-for-byte copies of the selected emitted RTL.
- `closure_synth.tcl` applies the clock and zero-delay I/O constraints **before**
  synthesis, then performs a fresh out-of-context implementation.
- `preflight_probe.sv`, `run_preflight.py`, and `preflight/` pin a synthetic
  non-Study-2 check of every Vivado Tcl capability used by the closure flow.
- `preflight_attempt1_unsupported_queries/` preserves the initial synthetic
  failure that discovered unsupported query forms and XDC conditionals. Its
  retained verbose timing report motivated the supported `check_timing` parser;
  no Study 2 candidate had been run.
- `preflight_attempt2_empty_get_timing_paths/` preserves the second synthetic
  failure: constraint coverage passed, but an empty Tcl path collection
  contradicted the retained Design Timing Summary. The final flow parses that
  summary's WNS and setup-endpoint count directly.
- `preflight_history.json` hashes every retained file after those two failed
  attempt directories were relocated; their original attestations remain
  byte-for-byte unchanged.
- `run_closure.py` performs bracketing and bisection in clean per-trial folders.
- `validate_gate.py` verifies hashes and produces the fail-closed pilot verdict.
- `test_workflow.py` exercises deterministic selection, planning, statistics,
  and static constraint-order checks without invoking Vivado.

## Freeze and check

Before the final manifest freeze, run the synthetic capability probe once:

```powershell
python timing_closure_gate_v1/run_preflight.py --run `
  --vivado "C:\Xilinx\Vivado\2023.1\bin\vivado.bat"
python timing_closure_gate_v1/run_preflight.py --check
```

The final manifest is then created with:

```powershell
python timing_closure_gate_v1/generate_manifest.py --write
python timing_closure_gate_v1/generate_manifest.py --check
python -m unittest -v timing_closure_gate_v1.test_workflow
```

Once `manifest.json` exists, `--write` refuses any change unless the recomputed
content is byte-identical. Never delete or replace it after inspecting a
closure result. Any justified protocol revision must use a new directory and
must retain this v1 outcome.

## Inspect without running Vivado

```powershell
python timing_closure_gate_v1/run_closure.py --dry-run
python timing_closure_gate_v1/validate_gate.py --check-manifest
```

## Execute the pilot

Vivado 2023.1 is available only on the Windows laptop. Run one Vivado process
at a time; the GPU servers and PYNQ board do not participate.

```powershell
python timing_closure_gate_v1/run_closure.py `
  --vivado "C:\Xilinx\Vivado\2023.1\bin\vivado.bat"

python timing_closure_gate_v1/validate_gate.py --scope pilot
```

The final contract is `results/pilot_gate.json`. Downstream experiments must
fail closed unless it contains the frozen manifest digest, all ten candidates,
`verdict: "PASS"`, and every criterion is true.

## Interpretation

A pass validates the old WNS-derived metric as a proxy on this predeclared
subset; it does not retroactively make every old value "timing-closed." A
failure is preserved. No post-hoc calibration of the headline is allowed. The
paper must then either replace the endpoint with exhaustive closure results or
downgrade/reframe the physical-performance claim as specified in the
preregistration.
