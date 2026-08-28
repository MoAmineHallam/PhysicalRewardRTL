# Explicit-tempDir diagnostic

Attempt 1 at `C:\VGT3D001` tested only a nested `cmd.exe` wrapper. The wrapper
failed before Vivado launched, so it is retained as launcher evidence and has
no bearing on tool stability.

Attempt 2 at `C:\VGT3D002` launched Vivado 2023.1 with a working directory of
`C:\VGT3D002\w` and explicit `-tempDir C:\VGT3D002\t`. During synthesis the
transient tree was observed under
`C:\VGT3D002\t\.Xil_Amine\Vivado-58620-Amine`, including the generated
`realtime\timing_gate_v2_stability_probe.tcl`. Vivado removed the transient
contents after normal exit.

The full synthetic implementation passed: compiled and implemented are one,
route status is clean, 51 setup paths are present, no timing path is
unconstrained, and WNS is 7.501 ns at a 10 ns request. This diagnostic contains
no Study-2 candidate RTL and is not itself the v3 stability gate.
