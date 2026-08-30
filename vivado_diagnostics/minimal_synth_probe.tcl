# Diagnostic only: exercises the Vivado synthesis helper on trivial RTL.
# This is deliberately separate from every frozen paper protocol.

if {$argc < 2 || $argc > 4} {
    puts stderr "usage: minimal_synth_probe.tcl SOURCE RESULT_FILE ?RT_COPY_ROOT|NOHELPER? ?NOHELPER?"
    exit 64
}

set source_file [file normalize [lindex $argv 0]]
set result_file [file normalize [lindex $argv 1]]
set disable_helper 0
set rt_copy_root ""
if {$argc >= 3} {
    set third [lindex $argv 2]
    if {$third eq "NOHELPER"} {
        set disable_helper 1
    } else {
        set rt_copy_root [file normalize $third]
    }
}
if {$argc == 4} {
    if {[lindex $argv 3] ne "NOHELPER"} {
        puts stderr "fourth argument must be NOHELPER"
        exit 64
    }
    set disable_helper 1
}
if {$rt_copy_root ne ""} {
    set ::env(HRT_TCL_PATH) [file join $rt_copy_root fpga_tcl]
    set ::env(RT_TCL_PATH) [file join $rt_copy_root base_tcl tcl]
    set ::env(RT_LIBPATH) [file join $rt_copy_root data]
    puts "DIAGNOSTIC_RT_OVERRIDE root=$rt_copy_root"
}
set_param general.maxThreads 1
if {$disable_helper} {
    set builtin_before [info exists ::env(BUILTIN_SYNTH)]
    if {$builtin_before} {
        unset ::env(BUILTIN_SYNTH)
    }
    puts "DIAGNOSTIC_BUILTIN_SYNTH_UNSET existed_before=$builtin_before exists_after=[info exists ::env(BUILTIN_SYNTH)]"
}

foreach name [lsort [array names ::env]] {
    if {[regexp {^(BUILTIN_SYNTH|HRT|RT|RDI|XILINX|TEMP|TMP)} $name]} {
        puts "PARENT_ENV $name=$::env($name)"
    }
}

if {[catch {
    read_verilog -sv $source_file
    synth_design -top minimal_probe -part xc7z020clg400-1 -mode out_of_context
} message options]} {
    set fh [open $result_file w]
    puts $fh "SYNTH_FAIL"
    puts $fh "MESSAGE=$message"
    puts $fh "OPTIONS=$options"
    close $fh
    puts stderr "SYNTH_FAIL message=$message"
    puts stderr "OPTIONS=$options"
    exit 2
}

set fh [open $result_file w]
puts $fh "SYNTH_PASS"
puts $fh "cells=[llength [get_cells -hierarchical]]"
close $fh
puts "SYNTH_PASS cells=[llength [get_cells -hierarchical]]"
exit 0
