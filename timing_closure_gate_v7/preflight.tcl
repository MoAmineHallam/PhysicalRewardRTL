# Non-synthesis preflight for the prospectively frozen Vivado 2026.1 gate.
set observed_version [version -short]
if {![string match "2026.1*" $observed_version]} {
    puts stderr "V7_PREFLIGHT_FAIL version=$observed_version"
    exit 2
}
set target_parts [get_parts -quiet xc7z020clg400-1]
if {[llength $target_parts] != 1} {
    puts stderr "V7_PREFLIGHT_FAIL part_count=[llength $target_parts]"
    exit 3
}
puts "V7_PREFLIGHT_PASS version=$observed_version part=[lindex $target_parts 0]"
exit 0
