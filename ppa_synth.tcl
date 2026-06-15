# ppa_synth.tcl  -  Out-of-context synth+impl of ONE RTL candidate -> PPA JSON.
#
# Runs on the laptop (Vivado 2023.1); no board needed. These are
# post-implementation CAD metrics (timing, area, estimated power) that a
# functional simulator like iverilog fundamentally cannot produce -- the
# basis for a hardware-grounded physical reward on top of functional
# correctness.
#
#   vivado -mode batch -source ppa_synth.tcl -tclargs \
#       <cand.v> <TopModule> <clk_port> <period_ns> <out.json>
#
# Emits one JSON line:
#   {"compiled":1,"wns":<ns>,"fmax_mhz":<>,"lut":<>,"ff":<>,"dsp":<>,
#    "bram":<>,"power_w":<>}
# or {"compiled":0} if synthesis fails (treat as physical reward 0).
#
# Notes:
#  - out_of_context mode: synthesizes the module alone (no I/O buffers, no
#    PS7), which is what you want for module-level PPA comparison.
#  - WNS via get_property SLACK on the worst setup path; fmax derived from
#    the constrained period. A combinational-only design reports no clock
#    path -> wns 0, fmax 0 (filter those out in analysis).
#  - LUT/FF/DSP/BRAM counted by primitive REF_NAME (robust, no report
#    parsing -- the Vivado Tcl console has no unix tools).
#  - report_power here is Vivado's vectorless estimate; for switching-
#    activity-based power, feed a .saif from simulation (future work).

set vfile  [lindex $argv 0]
set top    [lindex $argv 1]
set clkp   [lindex $argv 2]
set period [lindex $argv 3]
set outf   [lindex $argv 4]
set part   xc7z020clg400-1

proc emit {outf d} {
    set items {}
    foreach {k v} $d { lappend items "\"$k\":$v" }
    set fh [open $outf w]
    puts $fh "{[join $items ,]}"
    close $fh
}

# -sv: VerilogEval candidates may use SystemVerilog; it's a superset, safe
# for the Verilog-2001 rtl_library designs too.
if {[catch {
    read_verilog -sv $vfile
    synth_design -top $top -part $part -mode out_of_context
} err]} {
    puts "SYNTH FAIL: $err"
    emit $outf [list compiled 0]
    exit 0
}

if {[llength [get_ports -quiet $clkp]]} {
    create_clock -name vclk -period $period [get_ports $clkp]
    # Constrain I/O so input->reg and reg->output paths are timed. Without
    # this, simple designs have only unconstrained I/O paths and SLACK comes
    # back empty (breaking Fmax). Zero delay => slack reflects the design's own
    # logic depth, consistently across candidates.
    set din [remove_from_collection [all_inputs] [get_ports $clkp]]
    if {[llength $din]} { set_input_delay -clock vclk 0.000 $din }
    set dout [all_outputs]
    if {[llength $dout]} { set_output_delay -clock vclk 0.000 $dout }
}
opt_design
place_design
route_design

set wns 0.0
set paths [get_timing_paths -max_paths 1 -nworst 1 -setup -quiet]
if {[llength $paths]} {
    set s [get_property SLACK [lindex $paths 0]]
    if {$s ne "" && [string is double -strict $s]} { set wns $s }
}
set achieved [expr {$period - $wns}]
set fmax [expr {$achieved > 0 ? 1000.0 / $achieved : 0}]

set lut  [llength [get_cells -hier -quiet -filter {REF_NAME =~ LUT*}]]
set ff   [llength [get_cells -hier -quiet -filter {REF_NAME =~ FD*}]]
set dsp  [llength [get_cells -hier -quiet -filter {REF_NAME =~ DSP*}]]
set bram [llength [get_cells -hier -quiet -filter {REF_NAME =~ RAMB*}]]

set power 0.0
if {![catch {report_power -return_string} prpt]} {
    if {[regexp {Total On-Chip Power \(W\)\s*\|\s*([0-9.]+)} $prpt -> p]} {
        set power $p
    }
}

emit $outf [list compiled 1 wns $wns fmax_mhz $fmax \
            lut $lut ff $ff dsp $dsp bram $bram power_w $power]
puts "PPA: wns=$wns fmax=$fmax lut=$lut ff=$ff dsp=$dsp power=$power"
exit 0
