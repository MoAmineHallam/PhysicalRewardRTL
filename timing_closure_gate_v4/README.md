# Vivado single-thread infrastructure gate V4

V3's synthetic gate passed 20/20, but its subsequent frozen ten-candidate
pilot failed when multithreaded synthesis twice reported different existing
Vivado installation Tcl files as missing.  V4 is a prospective infrastructure
repair, not a reinterpretation or deletion of that failed result.

The only execution change is `set_param general.maxThreads 1`, applied by
`closure_synth_single_thread.tcl` before it sources the byte-identical V1
closure flow.  V4 also hashes the complete Vivado `scripts/rt/**/*.tcl` tree;
V3 covered only `scripts/rt/data/**/*.tcl`.

Before any Study-2 candidate can run under V4, twenty fresh synthetic
synth/place/route processes must pass on their first attempt.  A single invalid
measurement freezes a FAIL and blocks the V4 candidate package.

```powershell
python -m unittest timing_closure_gate_v4.test_stability -v
python timing_closure_gate_v4/freeze_dependency_baseline.py --check
python timing_closure_gate_v4/freeze_package.py --check
powershell -ExecutionPolicy Bypass -File .\launch_timing_stability_v4.ps1
```
