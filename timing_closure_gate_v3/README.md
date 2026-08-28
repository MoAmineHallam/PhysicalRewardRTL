# Timing-closure gate v3

V3 is a pre-candidate infrastructure repair after the irreversible v2
synthetic gate failed on first attempt 10. V2 remains retained and failed. No
Study-2 candidate ran in v2, and v3 does not reuse any v1 or v2 candidate
outcome.

The scientific protocol is unchanged: the same ten frozen candidates, RTL
hashes, device, Vivado 2023.1 closure Tcl, timing constraints, period search,
failure scoring, and pilot thresholds apply. The infrastructure amendment is
limited to Vivado transient storage. Every fresh process gets a unique short
working directory and an explicit short `-tempDir` under `C:\VGT3S001`, so
Vivado does not create its `.Xil/realtime` files under the long repository
path.

Before any candidate, 20 consecutive fresh full synth/place/route runs of the
synthetic probe must pass on their first attempt. Raw hashes of the Vivado
executable and installed Tcl dependency set are checked three times before and
after every process. There is no retry in this gate. Any failure freezes a FAIL
attestation and blocks candidate execution.

Verification commands:

```text
python -m unittest timing_closure_gate_v3.test_stability -v
python timing_closure_gate_v3/freeze_dependency_baseline.py --check
python timing_closure_gate_v3/freeze_package.py --check
```

The only command authorized to start the twenty-process gate is:

```powershell
powershell -ExecutionPolicy Bypass -File .\launch_timing_stability_v3.ps1
```
