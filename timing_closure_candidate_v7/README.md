# Real-candidate timing-closure pilot V7

This package is prepared while the prospective Vivado-2026.1 synthetic gate
V7 is running.  It cannot be frozen or launched unless that gate publishes an
immutable 40/40 PASS.  Preparation exposes no Study-2 candidate to Vivado.

After a V7 PASS, the package reruns all ten candidates frozen in
`timing_closure_gate_v1/manifest.json`, in their original order and from fresh
directories.  It imports the byte-identical V1 `close_candidate` function
directly, so the 0.75/1.25 initial bracket, expansion limits, ten bisections,
one-percent stopping rule, boundary confirmations, one invalid-measurement
retry, failure-zero rule, and four pilot thresholds are not reimplemented.

The only execution amendment is the validated side-by-side Vivado 2026.1
installation and its V7 raw dependency baseline.  V1--V6 candidate and gate
outcomes remain immutable and are not inputs to the measurements.

After the V7 attestation digest is inserted in `common.py`, the package must be
tested, frozen, and committed before the first candidate process.  Its only
authorized launcher is:

```powershell
powershell -ExecutionPolicy Bypass -File .\launch_timing_candidates_v7.ps1
```
