# Diagnostic only: prove non-project design/file cleanup inside one Vivado parent.
if {$argc != 2} {
    puts stderr "usage: persistent_two_run_probe.tcl SOURCE RESULT_FILE"
    exit 64
}
set source_file [file normalize [lindex $argv 0]]
set result_file [file normalize [lindex $argv 1]]
set_param general.maxThreads 1
set handle [open $result_file w]
set all_ok 1
for {set iteration 1} {$iteration <= 2} {incr iteration} {
    set files_before [llength [get_files -quiet]]
    set designs_before [llength [get_designs -quiet]]
    set iteration_ok 1
    set message ""
    if {$files_before != 0 || $designs_before != 0} {
        set iteration_ok 0
        set message "nonempty state before iteration"
    } elseif {[catch {
        read_verilog -sv $source_file
        synth_design -top minimal_probe -part xc7z020clg400-1 -mode out_of_context
    } message]} {
        set iteration_ok 0
    }
    catch {close_design}
    set retained [get_files -quiet]
    if {[llength $retained] > 0} {
        remove_files -quiet $retained
    }
    set files_after [llength [get_files -quiet]]
    set designs_after [llength [get_designs -quiet]]
    if {$files_after != 0 || $designs_after != 0} {
        set iteration_ok 0
        append message " cleanup_failed"
    }
    puts $handle "iteration=$iteration ok=$iteration_ok files_before=$files_before designs_before=$designs_before files_after=$files_after designs_after=$designs_after message=$message"
    flush $handle
    if {!$iteration_ok} {
        set all_ok 0
        break
    }
}
close $handle
puts "PERSISTENT_TWO_RUN_PASS=$all_ok"
exit [expr {$all_ok ? 0 : 2}]
