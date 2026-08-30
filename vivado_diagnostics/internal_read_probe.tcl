# Diagnostic only: this file is outside every frozen paper protocol.
# It repeatedly opens and reads one Vivado installation Tcl file without
# invoking synthesis, so a failure isolates the parent Tcl/file-I/O layer.

if {$argc != 2} {
    puts stderr "usage: internal_read_probe.tcl TARGET ITERATIONS"
    exit 64
}

set target [lindex $argv 0]
set iterations [lindex $argv 1]
if {![string is integer -strict $iterations] || $iterations < 1} {
    puts stderr "ITERATIONS must be a positive integer"
    exit 64
}

for {set i 1} {$i <= $iterations} {incr i} {
    if {[catch {
        set fh [open $target r]
        fconfigure $fh -translation binary
        set payload [read $fh]
        close $fh
    } message options]} {
        catch {close $fh}
        puts stderr "READ_FAIL iteration=$i target=$target message=$message"
        puts stderr "OPTIONS=$options"
        exit 2
    }
    if {[string length $payload] == 0} {
        puts stderr "READ_FAIL iteration=$i target=$target message=empty_file"
        exit 3
    }
}

puts "READ_PASS iterations=$iterations bytes=[string length $payload] target=$target"
exit 0
