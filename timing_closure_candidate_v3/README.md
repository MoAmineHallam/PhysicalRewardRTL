# Real-candidate timing-closure pilot V3

This package executes the ten candidates frozen in
`timing_closure_gate_v1/manifest.json` after the independent V3 infrastructure
gate passed 20 consecutive fresh Vivado implementations. It does not read or
reuse any V1/V2 candidate outcome.

The scientific protocol is unchanged from V1: the same candidates, device,
constraints, fresh-process period search, failure scoring, and four pilot
thresholds apply. The only operational amendment is the V3 repair: every
Vivado process uses a unique short work directory and explicit short
`-tempDir`, with the frozen Vivado dependency set checked three times before
and after every process.

Before execution:

```powershell
python -m unittest timing_closure_candidate_v3.test_candidate -v
python timing_closure_candidate_v3/freeze_package.py --check
python timing_closure_candidate_v3/run_candidates.py --dry-run
```

The only authorized launcher is:

```powershell
powershell -ExecutionPolicy Bypass -File .\launch_timing_candidates_v3.ps1
```

The final machine-readable verdict is
`timing_closure_candidate_v3/results/pilot_gate.json`. A PASS validates the
old WNS-derived value as a proxy on this predeclared subset; it does not make
every historical value timing-closed. A FAIL is retained and blocks physical
comparisons that depend on the old proxy.
