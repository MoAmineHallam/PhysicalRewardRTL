# Fresh constraint-driven implementation for timing_closure_gate_v1.
#
# Unlike the historical ppa_synth.tcl, this flow writes and reads the clock and
# zero-delay I/O XDC before synth_design. Every invocation runs in a fresh
# directory managed by run_closure.py.
#
# argv: <rtl> <top> <clock-port> <period-ns> <result-json> <report-dir> <part>

set vfile      [file normalize [lindex $argv 0]]
set top        [lindex $argv 1]
set clkp       [lindex $argv 2]
set period     [lindex $argv 3]
set outf       [file normalize [lindex $argv 4]]
set report_dir [file normalize [lindex $argv 5]]
set part       [lindex $argv 6]

file mkdir $report_dir

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
    set handle [open [file join $report_dir error.txt] w]
    puts $handle "stage=$stage"
    puts $handle $message
    close $handle
}

proc emit_failure {outf stage_code compiled implemented period} {
    emit_numeric_json $outf [list schema_version 1 stage_code $stage_code \
        compiled $compiled implemented $implemented period_ns $period \
        clock_count 0 setup_path_count 0 unconstrained_path_count -1 \
        unrouted_net_count -1 route_clean 0 constraint_coverage_ok 0 \
        wns_ns 0.0 closed 0]
}

if {![string is double -strict $period] || $period <= 0.0} {
    write_error $report_dir arguments "period must be a positive number"
    emit_failure $outf 1 0 0 0.0
    exit 0
}

# The generated XDC is itself retained with every trial. Reading it before
# synth_design is the critical methodological difference from ppa_synth.tcl.
set xdc [file join $report_dir constraints.xdc]
set xh [open $xdc w]
puts $xh "create_clock -name vclk -period $period \[get_ports {$clkp}\]"
puts $xh "set_input_delay -clock \[get_clocks vclk\] 0.000 \[get_ports -quiet -filter {DIRECTION == IN && NAME != $clkp}\]"
puts $xh {set_output_delay -clock [get_clocks vclk] 0.000 [get_ports -quiet -filter {DIRECTION == OUT}]}
close $xh

if {[catch {
    read_verilog -sv $vfile
    read_xdc $xdc
    synth_design -top $top -part $part -mode out_of_context
} err]} {
    write_error $report_dir synth $err
    emit_failure $outf 2 0 0 $period
    exit 0
}

report_clocks -file [file join $report_dir clocks_post_synth.rpt]
report_compile_order -used_in synthesis -file [file join $report_dir compile_order.rpt]

if {[catch {
    opt_design
    place_design
    route_design
} err]} {
    write_error $report_dir implementation $err
    emit_failure $outf 3 1 0 $period
    exit 0
}

report_route_status -file [file join $report_dir route_status.rpt]
set timing_report [file join $report_dir timing_summary.rpt]
report_timing_summary -delay_type max -max_paths 10 -report_unconstrained \
    -check_timing_verbose -warn_on_violation \
    -file $timing_report
report_utilization -file [file join $report_dir utilization.rpt]

set clocks [get_clocks -quiet vclk]
set clock_count [llength $clocks]
set wns 0.0
set setup_path_count 0

# Vivado 2023.1 does not provide get_timing_paths -unconstrained or the
# get_input_delays/get_output_delays query forms. Its supported, retained
# authority is report_timing_summary -report_unconstrained with verbose
# check_timing counts. Parse the named counts fail-closed; the synthetic
# capability preflight pins this exact behavior before candidate execution.
proc check_count {text name} {
    set pattern [format {checking %s \(([0-9]+)\)} $name]
    if {[regexp $pattern $text -> value]} {
        return $value
    }
    return -1
}
set th [open $timing_report r]
set timing_text [read $th]
close $th

# Parse the first Design Timing Summary data row. This retained report is more
# stable in Vivado 2023.1 than get_timing_paths -setup, which the synthetic
# preflight showed can return an empty collection despite reported endpoints.
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
set input_delay_count [expr {$no_input_delay_count >= 0 ? \
    [llength $nonclock_inputs] - $no_input_delay_count : -1}]
set output_delay_count [expr {$no_output_delay_count >= 0 ? \
    [llength $all_outputs] - $no_output_delay_count : -1}]
set constraint_coverage_ok [expr {
    $check_parse_ok &&
    $unconstrained_path_count == 0 &&
    $input_delay_count == [llength $nonclock_inputs] &&
    $output_delay_count == [llength $all_outputs]
}]

set closed [expr {
    $clock_count == 1 &&
    $setup_path_count > 0 &&
    $unconstrained_path_count == 0 &&
    $route_clean == 1 &&
    $constraint_coverage_ok == 1 &&
    $wns >= 0.0
}]

emit_numeric_json $outf [list schema_version 1 stage_code 0 compiled 1 \
    implemented 1 period_ns $period clock_count $clock_count \
    setup_path_count $setup_path_count \
    unconstrained_path_count $unconstrained_path_count \
    unrouted_net_count $unrouted_net_count route_clean $route_clean \
    nonclock_input_count [llength $nonclock_inputs] \
    output_count [llength $all_outputs] input_delay_count $input_delay_count \
    output_delay_count $output_delay_count \
    summary_parse_ok $summary_parse_ok \
    no_clock_count $no_clock_count \
    unconstrained_internal_count $unconstrained_internal_count \
    no_input_delay_count $no_input_delay_count \
    no_output_delay_count $no_output_delay_count \
    partial_input_delay_count $partial_input_delay_count \
    partial_output_delay_count $partial_output_delay_count \
    constraint_coverage_ok $constraint_coverage_ok wns_ns $wns \
    closed $closed]

puts "CLOSURE_GATE: period=$period wns=$wns closed=$closed clocks=$clock_count paths=$setup_path_count unconstrained=$unconstrained_path_count unrouted=$unrouted_net_count coverage=$constraint_coverage_ok"
exit 0
