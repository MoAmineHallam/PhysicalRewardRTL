# Vivado post-restart infrastructure gate V5

V1--V4 are immutable failed studies.  The minimal reproducer subsequently
showed that ordinary Vivado synthesis itself intermittently failed on this
Windows host, while the first helper-enabled probe after a Windows restart
passed.  V5 prospectively tests the bounded hypothesis that a freshly restarted
host is stable enough for the existing closure flow.

V5 does not modify Vivado, candidate RTL, constraints, the target device, or
the closure algorithm.  It reuses the byte-identical V4 single-thread wrapper
and synthetic probe.  The launcher must start within four hours of Windows
boot, with no other Vivado process.  The gate requires forty consecutive fresh
first-attempt synth/place/route processes, twice the earlier V3 requirement and
beyond V4's failure at run 19.  There are no retries.  One invalid measurement
freezes a FAIL and exposes no Study-2 candidate.

The package must be committed before launch.  The only authorized command is:

```powershell
powershell -ExecutionPolicy Bypass -File .\launch_timing_stability_v5.ps1
```

A PASS authorizes freezing a separate V5 ten-candidate package.  It does not
authorize reuse of any V1--V4 candidate outcome or directly validate a paper
endpoint.
