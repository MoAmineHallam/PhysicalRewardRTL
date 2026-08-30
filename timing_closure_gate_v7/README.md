# Vivado 2026.1 infrastructure gate V7

V1--V6 remain immutable studies.  V5 showed that restarting Windows did not
repair the intermittent Vivado 2023.1 internal-file reads, and V6 showed that a
persistent parent process did not repair them either.  The diagnosed host was
running Windows 11 25H2, which Vivado 2023.1 did not support.  A clean Vivado
2026.1 installation now exists side by side under `C:\AMD`; AMD lists Windows
11 25H2 and all Zynq-7000 devices as supported for that release.

V7 prospectively tests the single justified infrastructure change: Vivado
2023.1 is replaced by Vivado 2026.1 for execution.  It uses the byte-identical
V1 closure Tcl and V4 synthetic probe, the same `xc7z020clg400-1` target,
10-ns clock and zero-delay I/O constraints, fresh short work/temp directories,
and the same measurement-validity checks.  Unlike V4--V6, it does not disable
the ordinary synthesis helper or reuse a persistent parent; this tests the
actual fresh-process architecture intended for a later candidate package.

Before launch, the package pins raw bytes for the 2026.1 launcher, executable,
and complete `scripts/rt/**/*.tcl` tree.  A non-synthesis Tcl preflight checks
the exact Vivado version and target-part database.  The gate then requires
forty consecutive fresh first-attempt synth/place/route measurements.  There
are no retries.  One invalid measurement freezes a FAIL and exposes no Study-2
candidate.

The package must be committed before launch.  The only authorized command is:

```powershell
powershell -ExecutionPolicy Bypass -File .\launch_timing_stability_v7.ps1
```

A PASS authorizes freezing a separate V7 all-ten candidate package.  It does
not revive V1--V6, authorize reuse of V3 candidate outcomes, or directly
validate a manuscript frequency endpoint.
