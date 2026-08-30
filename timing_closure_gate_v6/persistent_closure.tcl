# V6 persistent-parent stability flow.
#
# Each iteration uses a separate documented in-memory Vivado project.  The
# scientific command sequence and result schema follow the V1 closure flow;
# only parent-process lifetime changes to avoid repeated helper initialization.
# argv: <rtl> <top> <clock-port> <period-ns> <result-root> <iterations> <part>

if {$argc != 7} {
    puts stderr "usage: persistent_closure.tcl RTL TOP CLOCK PERIOD RESULT_ROOT ITERATIONS PART"
    exit 64
}
set vfile       [file normalize [lindex $argv 0]]
set top         [lindex $argv 1]
set clkp        [lindex $argv 2]
set period      [lindex $argv 3]
set result_root [file normalize [lindex $argv 4]]
set iterations  [lindex $argv 5]
set part        [lindex $argv 6]

set_param general.maxThreads 1

proc emit_numeric_json {outf values} {
    set items {}
    foreach {key value} $values {
        lappend items "\"$key\":$value"
    }
    set handle [open $outf w]
    puts $handle "{[join $items ,]}"
    close $handle
}

proc write_error {report_dir stage message} {
    file mkdir $report_dir
    set handle [open [file join $report_dir error.txt] w]
    puts $handle "stage=$stage"
    puts $handle $message
    close $handle
}

proc check_count {text name} {
    set pattern [format {checking %s \(([0-9]+)\)} $name]
    if {[regexp $pattern $text -> value]} {
        return $value
    }
    return -1
}

proc clear_current_project {} {
    catch {close_project}
}

proc emit_failure {outf stage_code compiled implemented period iteration projects_before projects_after files_before files_after} {
    set isolation_ok [expr {$projects_before == 0 && $projects_after == 0 && $files_before == 0 && $files_after == 0}]
    emit_numeric_json $outf [list schema_version 2 stage_code $stage_code \
        compiled $compiled implemented $implemented period_ns $period \
        clock_count 0 setup_path_count 0 unconstrained_path_count -1 \
        unrouted_net_count -1 route_clean 0 constraint_coverage_ok 0 \
        summary_parse_ok 0 wns_ns 0.0 closed 0 iteration $iteration \
        projects_before $projects_before projects_after $projects_after \
        files_before $files_before files_after $files_after \
        session_isolation_ok $isolation_ok]
}

proc run_iteration {iteration vfile top clkp period result_root part} {
    set trial [file join $result_root [format "run_%02d" $iteration]]
    set report_dir [file join $trial reports]
    set outf [file join $trial vivado_result.json]
    file mkdir $report_dir
    set projects_before [llength [get_projects -quiet]]
    set files_before [llength [get_files -quiet]]
    if {$projects_before != 0 || $files_before != 0} {
        write_error $report_dir isolation "nonempty Vivado state before iteration"
        clear_current_project
        set projects_after [llength [get_projects -quiet]]
        set files_after [llength [get_files -quiet]]
        emit_failure $outf 4 0 0 $period $iteration $projects_before $projects_after $files_before $files_after
        return 0
    }

    if {![string is double -strict $period] || $period <= 0.0} {
        write_error $report_dir arguments "period must be a positive number"
        emit_failure $outf 1 0 0 0.0 $iteration $projects_before 0 $files_before 0
        return 0
    }

    set xdc [file join $report_dir constraints.xdc]
    set xh [open $xdc w]
    puts $xh "create_clock -name vclk -period $period \[get_ports {$clkp}\]"
    puts $xh "set_input_delay -clock \[get_clocks vclk\] 0.000 \[get_ports -quiet -filter {DIRECTION == IN && NAME != $clkp}\]"
    puts $xh {set_output_delay -clock [get_clocks vclk] 0.000 [get_ports -quiet -filter {DIRECTION == OUT}]}
    close $xh

    if {[catch {
        create_project -in_memory persistent_v6_$iteration -part $part
        read_verilog -sv $vfile
        read_xdc $xdc
        synth_design -top $top -part $part -mode out_of_context
    } err]} {
        write_error $report_dir synth $err
        clear_current_project
        set projects_after [llength [get_projects -quiet]]
        set files_after [llength [get_files -quiet]]
        emit_failure $outf 2 0 0 $period $iteration $projects_before $projects_after $files_before $files_after
        return 0
    }

    report_clocks -file [file join $report_dir clocks_post_synth.rpt]
    report_compile_order -used_in synthesis -file [file join $report_dir compile_order.rpt]
    if {[catch {
        opt_design
        place_design
        route_design
    } err]} {
        write_error $report_dir implementation $err
        clear_current_project
        set projects_after [llength [get_projects -quiet]]
        set files_after [llength [get_files -quiet]]
        emit_failure $outf 3 1 0 $period $iteration $projects_before $projects_after $files_before $files_after
        return 0
    }

    report_route_status -file [file join $report_dir route_status.rpt]
    set timing_report [file join $report_dir timing_summary.rpt]
    report_timing_summary -delay_type max -max_paths 10 -report_unconstrained \
        -check_timing_verbose -warn_on_violation -file $timing_report
    report_utilization -file [file join $report_dir utilization.rpt]

    set clocks [get_clocks -quiet vclk]
    set clock_count [llength $clocks]
    set wns 0.0
    set setup_path_count 0
    set th [open $timing_report r]
    set timing_text [read $th]
    close $th
    set summary_header_seen 0
    set summary_dash_seen 0
    set summary_parse_ok 0
    foreach line [split $timing_text "\n"] {
        if {!$summary_header_seen && [regexp {^\s*WNS\(ns\)} $line]} {
            set summary_header_seen 1
            continue
        }
        if {$summary_header_seen && !$summary_dash_seen} {
            if {[regexp {^\s*-+\s+} $line]} { set summary_dash_seen 1 }
            continue
        }
        if {$summary_dash_seen && [regexp {^\s*([-+]?[0-9]*\.?[0-9]+)\s+([-+]?[0-9]*\.?[0-9]+)\s+([0-9]+)\s+([0-9]+)} $line -> summary_wns summary_tns summary_failing summary_total]} {
            set wns $summary_wns
            set setup_path_count $summary_total
            set summary_parse_ok 1
            break
        }
    }
    set no_clock_count [check_count $timing_text no_clock]
    set unconstrained_internal_count [check_count $timing_text unconstrained_internal_endpoints]
    set no_input_delay_count [check_count $timing_text no_input_delay]
    set no_output_delay_count [check_count $timing_text no_output_delay]
    set partial_input_delay_count [check_count $timing_text partial_input_delay]
    set partial_output_delay_count [check_count $timing_text partial_output_delay]
    set check_counts [list $no_clock_count $unconstrained_internal_count \
        $no_input_delay_count $no_output_delay_count $partial_input_delay_count \
        $partial_output_delay_count]
    set check_parse_ok 1
    foreach value $check_counts {
        if {$value < 0} { set check_parse_ok 0 }
    }
    set unconstrained_path_count -1
    if {$check_parse_ok} {
        set unconstrained_path_count 0
        foreach value $check_counts {
            set unconstrained_path_count [expr {$unconstrained_path_count + $value}]
        }
    }
    set unrouted_net_count -1
    if {![catch {
        set unrouted_nets [get_nets -hier -quiet -filter {ROUTE_STATUS == UNROUTED}]
    }]} {
        set unrouted_net_count [llength $unrouted_nets]
    }
    set route_clean [expr {$unrouted_net_count == 0 ? 1 : 0}]
    set nonclock_inputs [get_ports -quiet -filter "DIRECTION == IN && NAME != $clkp"]
    set all_outputs [get_ports -quiet -filter {DIRECTION == OUT}]
    set nonclock_input_count [llength $nonclock_inputs]
    set output_count [llength $all_outputs]
    set input_delay_count [expr {$no_input_delay_count >= 0 ? $nonclock_input_count - $no_input_delay_count : -1}]
    set output_delay_count [expr {$no_output_delay_count >= 0 ? $output_count - $no_output_delay_count : -1}]
    set constraint_coverage_ok [expr {$check_parse_ok && $unconstrained_path_count == 0 && $input_delay_count == $nonclock_input_count && $output_delay_count == $output_count}]
    set closed [expr {$clock_count == 1 && $setup_path_count > 0 && $unconstrained_path_count == 0 && $route_clean == 1 && $constraint_coverage_ok == 1 && $wns >= 0.0}]

    clear_current_project
    set projects_after [llength [get_projects -quiet]]
    set files_after [llength [get_files -quiet]]
    set isolation_ok [expr {$projects_before == 0 && $projects_after == 0 && $files_before == 0 && $files_after == 0}]
    emit_numeric_json $outf [list schema_version 2 stage_code 0 compiled 1 \
        implemented 1 period_ns $period clock_count $clock_count \
        setup_path_count $setup_path_count unconstrained_path_count $unconstrained_path_count \
        unrouted_net_count $unrouted_net_count route_clean $route_clean \
        nonclock_input_count $nonclock_input_count output_count $output_count \
        input_delay_count $input_delay_count output_delay_count $output_delay_count \
        summary_parse_ok $summary_parse_ok no_clock_count $no_clock_count \
        unconstrained_internal_count $unconstrained_internal_count \
        no_input_delay_count $no_input_delay_count no_output_delay_count $no_output_delay_count \
        partial_input_delay_count $partial_input_delay_count partial_output_delay_count $partial_output_delay_count \
        constraint_coverage_ok $constraint_coverage_ok wns_ns $wns closed $closed \
        iteration $iteration projects_before $projects_before projects_after $projects_after \
        files_before $files_before files_after $files_after session_isolation_ok $isolation_ok]
    puts "PERSISTENT_CLOSURE iteration=$iteration wns=$wns closed=$closed isolation=$isolation_ok"
    return [expr {$isolation_ok && $summary_parse_ok && $constraint_coverage_ok && $route_clean}]
}

if {![string is integer -strict $iterations] || $iterations < 1} {
    puts stderr "iterations must be a positive integer"
    exit 64
}
file mkdir $result_root
set completed 0
for {set iteration 1} {$iteration <= $iterations} {incr iteration} {
    if {![run_iteration $iteration $vfile $top $clkp $period $result_root $part]} {
        break
    }
    set completed $iteration
}
puts "PERSISTENT_SESSION_COMPLETED=$completed REQUESTED=$iterations"
exit [expr {$completed == $iterations ? 0 : 2}]
