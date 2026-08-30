# Diagnostic copy of Vivado 2023.1 rtSynthParallelPrep.tcl.
# The single behavioral change is the next line, which disables the helper
# process implicated by the minimal reproducer. Never install this into Vivado.
rt::set_parameter enableParallelHelperSpawn 0

set parallelNumProcs 4
if {[ info exists ::env(BUILTIN_SYNTH) ] } {
    set sm [get_param synth.maxThreads]
    set gm [get_param general.maxThreads]
    if { $sm < $gm } {
        set parallelNumProcs $sm
    } else {
        set parallelNumProcs $gm
    }
}
rt::init_pss_mem_watcher
rt::UMsg_tclMessage SYN 627 $parallelNumProcs

if {[ info exists ::env(BUILTIN_SYNTH) ] && [rt::get_parameter enableParallelHelperSpawn]} {
  set helperShmKey [rt::get_parameter helper_shm_key]
  if {$helperShmKey == "" && [$rt::db isSharedMemoryAvailable] } {
    rt::UMsg_tclMessage SYN 713
    rt::set_parameter helper_shm_key "LaunchHelperProcessKey_[pid]_[clock seconds]"
    set rt::helper_process_pid [rt::parallel_synth_helper_wrapper [rt::get_parameter helper_shm_key] $rt::partid [pid] ]
    rt::UMsg_tclMessage SYN 714 $rt::helper_process_pid
  }
} else {
  rt::set_parameter helper_shm_key "dummy"
}
