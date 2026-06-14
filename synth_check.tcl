# synth_check.tcl  -  Fast synthesizability screen for candidate RTL (laptop).
#
# One Vivado session, out-of-context synth of every candidate .v in a dir.
# Far faster than per-file vivado launches (no relaunch overhead) and skips
# place/route -- we only need to know which candidates Vivado will accept.
#
# Doubles as gap-study tier 1: a candidate that compiles in simulation
# (compile_ok in dataset.jsonl) but FAILS synthesis here is a sim/silicon
# discrepancy detectable without the board -- simulation rewarded RTL that
# cannot exist on hardware. The fails list also feeds
# gen_candidate_bitstream --exclude so the batch builds stop choking.
#
#   vivado -mode batch -source synth_check.tcl -tclargs \
#       rtl/cand_batches/cand rtl/cand_batches/synth.fails [part]
#
# Outputs:
#   <fails>         one failing module name per line (for --exclude)
#   <fails>.detail  "<module>\t<first error>" for categorising causes

set cand_dir [lindex $argv 0]
set out      [lindex $argv 1]
set part     [lindex $argv 2]
if {$part eq ""} { set part "xc7z020clg400-1" }

set files [lsort [concat [glob -nocomplain [file join $cand_dir *.sv]] \
                          [glob -nocomplain [file join $cand_dir *.v]]]]
set failfh [open $out w]
set detfh  [open $out.detail w]
set nfail 0
set nok 0

foreach f $files {
    set top [file rootname [file tail $f]]
    if {[catch {
        create_project -in_memory -part $part
        read_verilog -sv $f
        synth_design -top $top -mode out_of_context
    } err]} {
        puts $failfh $top
        flush $failfh
        regsub -all {\s+} $err " " emsg
        puts $detfh "$top\t[string range $emsg 0 250]"
        flush $detfh
        incr nfail
        puts "FAIL $top"
    } else {
        incr nok
        puts "OK   $top"
    }
    catch {close_project}
}
close $failfh
close $detfh
puts "DONE: [llength $files] checked, $nok ok, $nfail failed synthesis."
puts "Exclude list -> $out   (reasons -> $out.detail)"
