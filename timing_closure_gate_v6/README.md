# Vivado persistent-parent infrastructure gate V6

V1--V5 remain immutable failures.  V5 proved that restarting Windows did not
repair the intermittent Vivado internal-file fault.  Diagnostics then showed
that repeating non-project synthesis in one parent was not viable, but two
separate documented in-memory projects completed in one parent with clean
project boundaries and a single helper launch.

V6 prospectively tests that supported isolation architecture.  One Vivado
parent creates forty separate in-memory projects.  Each project reads the same
synthetic RTL and pre-synthesis XDC, then runs the V1 synth/opt/place/route and
report sequence.  It is closed before the next project.  The gate requires all
forty measurements, clean empty project/file state at every boundary, unchanged
raw Vivado dependencies, stable WNS within 0.001 ns, and exactly one helper
launch.  There are no process or iteration retries.

The package must be committed before launch.  The only authorized command is:

```powershell
powershell -ExecutionPolicy Bypass -File .\launch_timing_stability_v6.ps1
```

A PASS authorizes freezing a separate persistent-parent V6 candidate pilot;
it is not itself a paper endpoint.
