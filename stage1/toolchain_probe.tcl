# Read-only device inventory plus disposable, in-memory synthesis; no board access.
puts "FPGA2_VERSION [version -short]"
foreach pattern {xc7z020clg400-1 xczu5eg-sfvc784*} {
    puts "FPGA2_PARTS $pattern [get_parts -quiet $pattern]"
}
set src [file join [pwd] probe.v]
set handle [open $src w]
puts $handle {module fpga2_probe(input wire clk, input wire [15:0] a,b, output reg [16:0] y); always @(posedge clk) y <= {1'b0,a}+{1'b0,b}; endmodule}
close $handle
foreach part {xc7z020clg400-1 xczu5eg-sfvc784-1-e} {
    if {[llength [get_parts -quiet $part]] != 1} { error "Missing required part $part" }
    create_project -in_memory -part $part
    read_verilog $src
    synth_design -top fpga2_probe -part $part
    puts "FPGA2_SYNTH_OK $part CELLS [llength [get_cells -hierarchical]]"
    close_project
}
puts "FPGA2_PROBE_COMPLETE"
exit
