# Timing-closure gate v2

This is a pre-candidate repair of the v1 measurement gate. V1 is preserved as
an irreversible failure/abort because Vivado 2023.1 intermittently could not
read four distinct Tcl files from its own installation during synthesis
initialization. That is documented in `v1_failure_abort_report.json`; it is
not interpreted as RTL timing performance.

V2 reruns the original ten frozen candidates from scratch only after a
synthetic infrastructure gate passes. The candidate selection, RTL hashes,
clock-search algorithm, timing constraints, device, and thresholds are
unchanged. The new condition is operational: 20 identical raw-byte reads of
the Vivado executable/Tcl dependency set must establish a baseline, then 12
fresh full synth/place/route runs of a synthetic module must all pass while
three raw-byte dependency guards before and after each run remain identical.

Safe preparation and verification commands:

```text
python -m unittest timing_closure_gate_v2.test_stability -v
python timing_closure_gate_v2/audit_v1_abort.py --check
python timing_closure_gate_v2/freeze_dependency_baseline.py --write
python timing_closure_gate_v2/freeze_dependency_baseline.py --check
```

The only command that starts Vivado is the frozen operational wrapper:

```powershell
powershell -ExecutionPolicy Bypass -File .\launch_timing_stability_v2.ps1
```

It writes `stability_campaign_001/` only once, validates its twelve-run
attestation, and invokes the already-tested iPhone notification hook on either
PASS or FAIL. A FAIL is retained and blocks every Study-2 candidate. A PASS
does not itself establish any Study-2 result; it merely authorizes freezing the
separate v2 candidate-runner package.
