# V4 infrastructure wrapper for the unchanged V1 closure flow.
#
# V3 failed when Vivado's multithreaded synthesis helper twice reported two
# different existing internal Tcl files as missing.  V4 disables Vivado
# multithreading before sourcing the byte-identical V1 scientific flow.  The
# V1 argv, constraints, implementation stages, reports, and JSON schema remain
# unchanged.

set_param general.maxThreads 1
set original_flow [file normalize [file join [file dirname [info script]] .. timing_closure_gate_v1 closure_synth.tcl]]
source $original_flow
