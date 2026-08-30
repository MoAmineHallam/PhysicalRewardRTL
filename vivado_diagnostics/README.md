# Vivado 2023.1 Internal-Tcl Read Diagnostic

This package is diagnostic infrastructure only. It is outside every frozen
paper protocol and contains no Study-2 candidate RTL or scientific endpoint.

## Reproduction on 2026-08-30

The retained V4 error was reduced to `minimal_probe.sv`, a trivial registered
32-bit expression, and `minimal_synth_probe.tcl`, which invokes only
out-of-context synthesis for `xc7z020clg400-1`.

The ordinary file-I/O layer was stable:

- PowerShell performed 10,000 consecutive SHA-256 reads of
  `unimacro_vhdl.tcl` with zero failures.
- A single parent Vivado Tcl process performed 20,000 binary reads of the same
  file with zero failures.
- Five additional fresh parent Vivado Tcl processes each performed 100 reads
  with zero failures.

Minimal synthesis reproduced the fault. In the nine retained helper-enabled
runs, four passed and five failed. Failures falsely reported different existing
files as absent or unreadable, including `rtSynthCleanup.tcl`, `common.tcl`,
`lib_core.tcl`, `unimacro_vhdl.tcl`, and one freshly generated
`realtime/minimal_probe.tcl`. Copying the byte-identical Vivado realtime Tcl
tree to a shorter path did not eliminate the failure.

`rtSynthParallelPrep_nohelper.tcl` is a diagnostic copy that changes one
internal parameter to prevent the parallel helper launch. It must never be
installed into Vivado or used for paper measurements. It improved but did not
solve stability: six of seven retained no-helper runs passed, while the seventh
again falsely reported the existing `common.tcl` as missing. Therefore the
parallel helper amplifies the fault but is not its root cause.

The installed files remained byte-stable, their ACLs permitted reads, 10,000
post-failure hash reads succeeded, the C: NTFS volume reported Healthy/OK, and
no contemporaneous Defender detection, storage error, or resource-exhaustion
event explained the failures.

## Host compatibility boundary

The host runs Windows 11 25H2, build 26200.9168. AMD's Vivado 2023.1 release
notes support Windows 11 21H2 and 22H2, not 25H2:

https://docs.amd.com/r/2023.1-English/ug973-vivado-release-notes-install-license/Supported-Operating-Systems

The established proximate cause is intermittent file-I/O failure inside the
Vivado 2023.1 synthesis/realtime runtime on this host. The strongest underlying
hypothesis is the unsupported Vivado/Windows combination, but the retained
evidence cannot uniquely distinguish that from a Windows minifilter or other
host-runtime interaction.

## First post-restart trial (2026-08-30)

The prescribed first ordinary helper-enabled minimal synthesis was run once
after restarting Windows, before opening Vivado or launching any paper
experiment. It passed with 106 cells, zero synthesis errors, and an empty
stderr log. The retained stdout confirms that the synthesis helper was
launched, so this trial exercised the path implicated before the restart.
Raw output and metadata are under
`evidence/postrestart_20260830__r01/`.

This single pass does not establish that restarting repaired the intermittent
fault: four of the nine retained pre-restart helper-enabled runs also passed.
It therefore does not authorize a candidate experiment by itself.

## Subsequent prospective gates

V5 tested the restart hypothesis directly and froze FAIL after six valid fresh
synthetic implementations: process 7 again failed on the existing
`unimacro_vhdl.tcl`, with matching dependency hashes.  V6 then tested isolated
in-memory projects inside one persistent Vivado parent.  Its first full routed
project was valid, but synthesis of project 2 failed in ABC on an internal
realtime temporary path.  Raw evidence and immutable attestations are retained
under `timing_closure_gate_v5/` and `timing_closure_gate_v6/`.

These outcomes reject both reboot and persistent-parent execution as local
repairs.  No candidate was exposed.  The remaining defensible remedy is a
validated licensed Vivado environment on a supported operating system or a
different prospectively justified external environment.

## Next controlled action

1. Restart Windows, then run the minimal reproducer before opening Vivado or
   other heavy applications.
2. If the reproducer fails again, do not retry paper experiments. Run Vivado
   2023.1 on a supported Windows 11 22H2 or Ubuntu 22.04 environment.
3. Only after a newly frozen stability campaign passes may a new candidate
   closure study be authorized. V1--V4 remain immutable failures.

The `evidence/` directory retains stdout, stderr, and result files for the
bounded campaigns used in this diagnosis.
