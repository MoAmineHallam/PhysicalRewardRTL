# Instrument the unchanged historical script, intercepting only its exit.
set historical_script [lindex $argv 5]
set diagnostic_dir [lindex $argv 6]
file mkdir $diagnostic_dir
rename exit real_exit
proc exit {args} { error "HISTORICAL_EXIT" }
set source_status [catch {source $historical_script} source_message]
set fh [open [file join $diagnostic_dir source_status.txt] w]
puts $fh "catch_code=$source_status message=$source_message"
puts $fh "vivado=[version -short]"
close $fh
if {$source_message ne "HISTORICAL_EXIT"} { real_exit 2 }
if {![info exists paths]} { real_exit 3 }
set setup_count [llength [get_timing_paths -max_paths 1 -nworst 1 -setup -quiet]]
set clock_count [llength [get_clocks -quiet]]
emit [file join $diagnostic_dir path_diagnostic.json] [list clock_count $clock_count setup_path_count $setup_count historical_wns $wns historical_fmax_mhz $fmax lut $lut ff $ff dsp $dsp bram $bram]
set fh [open [file join $diagnostic_dir report_status.txt] w]
foreach {filename command} {
    check_timing.txt {check_timing -verbose -return_string}
    clocks.txt {report_clocks -return_string}
    utilization.txt {report_utilization -return_string}
    timing_summary.txt {report_timing_summary -report_unconstrained -return_string}
    route_status.txt {report_route_status -return_string}
    timing.txt {report_timing -max_paths 10 -return_string}
} {
    set status [catch {eval $command} result]
    puts $fh "$filename catch_code=$status"
    set report [open [file join $diagnostic_dir $filename] w]
    puts $report $result
    close $report
}
foreach {filename command} {
    routed.dcp {write_checkpoint}
    routed.v {write_verilog -mode funcsim}
    constraints.xdc {write_xdc}
} {
    set status [catch {eval $command [list [file join $diagnostic_dir $filename]]} result]
    puts $fh "$filename catch_code=$status message=$result"
}
close $fh
real_exit 0
