# Post-primary timing-path coverage audit V1

Freeze before broad replay; 2026-09-05. The known single SFT suspect has already
been replayed with Vivado 2026.1 and yielded no setup paths and a constant-zero
netlist. That finding motivates this explicitly post-primary diagnostic.

Include every emitted candidate from the original sealed SFT, RF seed 1, and RF
seed 2 directories (202 total across the original 20-design universe). Preserve
the original RTL, multiplicities, zero-correct design denominators, part,
5-ns request, and after-synthesis clock insertion. Candidate order is directory
order then module-name order, independent of new timing results. No selection
by new performance, no changes to original files or original primary interval.

Run the original `ppa_synth.tcl` through the already tested diagnostic wrapper,
using the validated Vivado 2026.1 installation with the V7 dependency guard
before and after each invocation, fresh short work/temp paths, and retained
stdout/stderr, reports, routed checkpoint/netlist, and constraints. A numeric
frequency requires an actual setup path; a missing path is explicitly labeled
INVALID_NO_SETUP_PATH, never accepted as 200 MHz. Any tool/parse/report failure
is INCONCLUSIVE, not a physical zero. Retry an inconclusive invocation once in
a fresh directory; retain both attempts. Stop on dependency drift or timeout.
Never use the better of two performance outcomes: only retry an inconclusive
measurement. Persist candidate completion before continuing; resumed execution
must validate frozen inputs and completed artifact hashes.

This is cross-version coverage/flow sensitivity, not exact reproduction of
Vivado 2023.1, period-bracketed closure, hold/pulse-width sign-off, or proof of
synthesized functional equivalence. Report all outcomes and arm-specific error
distributions after completion. Do not silently replace original frequencies
or pool this diagnostic into original confirmatory intervals. New seed physical
evaluation remains a separate stage after generation completion checks.
