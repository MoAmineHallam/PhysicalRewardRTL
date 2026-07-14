# Auto-generated - Phase D1 HLS baseline batch (Vitis HLS).
# Run from a SHORT path (Windows 260-char/8191-char-cmdline limit trips
# export_design on the larger designs). Recommended on the laptop:
#   subst X: C:\Users\Amine\mas\fpga-repo\rtl\hls_baseline
#   cd /d X:\
#   vitis_hls -f run_hls.tcl
# Resumable: solutions that already have an export report are skipped, and a
# failed export is caught so ONE failure never aborts the whole batch.
set PART   "xc7z020clg400-1"
set PERIOD 5.0
set DESIGNS [list]
lappend DESIGNS "fir6_8b"
lappend DESIGNS "firr6"
lappend DESIGNS "fir10_8b"
lappend DESIGNS "firr10"
lappend DESIGNS "fir18_8b"
lappend DESIGNS "firr18"
lappend DESIGNS "fir26_8b"
lappend DESIGNS "firr26"
lappend DESIGNS "fir36_8b"
lappend DESIGNS "firr36"
lappend DESIGNS "fir40_8b"
lappend DESIGNS "firr40"
lappend DESIGNS "poly7_8b"
lappend DESIGNS "poly7_v1_8b"
lappend DESIGNS "poly7_v2_8b"
lappend DESIGNS "poly7_v3_8b"
lappend DESIGNS "poly7_v4_8b"
lappend DESIGNS "poly7_v5_8b"
lappend DESIGNS "poly4_v6_8b"
lappend DESIGNS "poly4_v7_8b"
lappend DESIGNS "poly8_v6_8b"
lappend DESIGNS "poly8_v7_8b"

set FAILED [list]
foreach d $DESIGNS {
    foreach variant {pragma nopragma} {
        set proj "proj_${d}_${variant}"
        set rpt  "$proj/sol1/impl/report/verilog/${d}_export.rpt"
        if {[file exists $rpt]} {
            puts "SKIP $d/$variant (already done)"
            continue
        }
        puts ">>> $d / $variant"
        open_project -reset $proj
        set_top $d
        if {$variant eq "nopragma"} {
            add_files "$d.cpp" -cflags "-DNO_PRAGMA"
        } else {
            add_files "$d.cpp"
        }
        add_files -tb "$d\_tb.cpp"
        open_solution -reset "sol1"
        set_part $PART
        create_clock -period $PERIOD
        csim_design
        csynth_design
        # catch so a single Windows cmdline-length export failure logs and the
        # batch keeps going instead of aborting mid-sweep
        if {[catch {export_design -flow impl -rtl verilog} emsg]} {
            puts "EXPORT-FAIL $d/$variant : $emsg"
            lappend FAILED "$d/$variant"
        }
        close_project
    }
}
puts "HLS BASELINE BATCH DONE"
if {[llength $FAILED]} {
    puts "EXPORTS THAT FAILED (rerun after `subst` to a short path): $FAILED"
}
exit
