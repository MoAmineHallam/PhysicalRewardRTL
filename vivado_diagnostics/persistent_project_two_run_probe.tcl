# Diagnostic only: test two isolated in-memory projects in one Vivado parent.
if {$argc != 2} {
    puts stderr "usage: persistent_project_two_run_probe.tcl SOURCE RESULT_FILE"
    exit 64
}
set source_file [file normalize [lindex $argv 0]]
set result_file [file normalize [lindex $argv 1]]
set_param general.maxThreads 1
set handle [open $result_file w]
set all_ok 1
for {set iteration 1} {$iteration <= 2} {incr iteration} {
    set projects_before [llength [get_projects -quiet]]
    set iteration_ok 1
    set message ""
    if {$projects_before != 0} {
        set iteration_ok 0
        set message "nonempty project state before iteration"
    } elseif {[catch {
        create_project -in_memory persistent_project_$iteration -part xc7z020clg400-1
        read_verilog -sv $source_file
        synth_design -top minimal_probe -part xc7z020clg400-1 -mode out_of_context
    } message]} {
        set iteration_ok 0
    }
    catch {close_project}
    set projects_after [llength [get_projects -quiet]]
    if {$projects_after != 0} {
        set iteration_ok 0
        append message " cleanup_failed"
    }
    puts $handle "iteration=$iteration ok=$iteration_ok projects_before=$projects_before projects_after=$projects_after message=$message"
    flush $handle
    if {!$iteration_ok} {
        set all_ok 0
        break
    }
}
close $handle
puts "PERSISTENT_PROJECT_TWO_RUN_PASS=$all_ok"
exit [expr {$all_ok ? 0 : 2}]
