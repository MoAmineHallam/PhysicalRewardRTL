# Generated symmetric held-out comparison bitstream.
set PART    "xc7z020clg400-1"
set CLK_MHZ 200
set ROOT    [file normalize [file join [file dirname [info script]] .. ..]]
set OUT     [file join $ROOT rtl holdout_silicon_symmetric out]
file mkdir $OUT

create_project sys_holdout_symmetric [file join $OUT proj] -part $PART -force
add_files [list \
    [file join $ROOT rtl la_axi_fast.v] \
    [file join $ROOT rtl holdout_silicon_symmetric dut_top_holdout.v] \
    [file join $ROOT rtl_library echo8b design.v] \
    [file join $ROOT rtl holdout_silicon_symmetric duts sft__fir26_8b__g3.v] \
    [file join $ROOT rtl holdout_silicon_symmetric duts grpo__fir26_8b__g0.v] \
    [file join $ROOT rtl holdout_silicon_symmetric duts sft__firr26__g2.v] \
    [file join $ROOT rtl holdout_silicon_symmetric duts grpo__firr26__g0.v] \
    [file join $ROOT rtl holdout_silicon_symmetric duts sft__poly7_8b__g0.v] \
    [file join $ROOT rtl holdout_silicon_symmetric duts grpo__poly7_8b__g0.v] \
    [file join $ROOT rtl holdout_silicon_symmetric duts sft__firr36__g0.v] \
    [file join $ROOT rtl holdout_silicon_symmetric duts grpo__firr36__g0.v] \
    [file join $ROOT rtl holdout_silicon_symmetric duts sft__poly8_v6_8b__g0.v] \
    [file join $ROOT rtl holdout_silicon_symmetric duts grpo__poly8_v6_8b__g0.v] ]
update_compile_order -fileset sources_1

create_bd_design "system"
create_bd_cell -type ip -vlnv xilinx.com:ip:processing_system7:5.5 ps7
apply_bd_automation -rule xilinx.com:bd_rule:processing_system7 \
    -config {make_external "FIXED_IO, DDR" apply_board_preset "1"} \
    [get_bd_cells ps7]
set_property -dict [list CONFIG.PCW_FPGA0_PERIPHERAL_FREQMHZ $CLK_MHZ] \
    [get_bd_cells ps7]
create_bd_cell -type module -reference la_axi_fast la0
create_bd_cell -type module -reference dut_top      dut0
apply_bd_automation -rule xilinx.com:bd_rule:axi4 \
    -config {Master "/ps7/M_AXI_GP0" Clk "Auto"} \
    [get_bd_intf_pins la0/S_AXI]
connect_bd_net [get_bd_pins la0/sel]       [get_bd_pins dut0/sel]
connect_bd_net [get_bd_pins la0/probe]     [get_bd_pins dut0/probe]
connect_bd_net [get_bd_pins la0/capturing] [get_bd_pins dut0/cap]
connect_bd_net [get_bd_pins dut0/clk]   [get_bd_pins la0/S_AXI_ACLK]
connect_bd_net [get_bd_pins dut0/rst_n] [get_bd_pins la0/S_AXI_ARESETN]
assign_bd_address
validate_bd_design
save_bd_design

set_property synth_checkpoint_mode None [get_files system.bd]
generate_target all [get_files system.bd]
make_wrapper -files [get_files system.bd] -top -force
add_files -norecurse [glob \
    [file join $OUT proj *.gen sources_1 bd system hdl system_wrapper.v] \
    [file join $OUT proj *.srcs sources_1 bd system hdl system_wrapper.v]]
set_property top system_wrapper [current_fileset]

# Run in this Vivado process. The Windows run-manager launcher uses WSH child
# processes, which can stall in managed sessions before synthesis starts.
# Reopen the project after generating module-reference wrappers. Without this
# boundary Vivado 2023.1 may auto-disable the referenced RTL in the same process,
# leaving the generated wrapper unable to resolve la_axi_fast during synthesis.
close_project
open_project [file join $OUT proj sys_holdout_symmetric.xpr]
update_compile_order -fileset sources_1
synth_design -top system_wrapper -part $PART -flatten_hierarchy rebuilt
write_checkpoint -force [file join $OUT post_synth.dcp]
report_utilization -file [file join $OUT utilization_post_synth.rpt]
opt_design
place_design
phys_opt_design
route_design
write_checkpoint -force [file join $OUT post_route.dcp]
report_route_status -file [file join $OUT route_status.rpt]
report_timing_summary -delay_type max -max_paths 20 \
    -file [file join $OUT timing_summary_routed.rpt]
report_utilization -file [file join $OUT utilization_routed.rpt]
set worst_path [get_timing_paths -delay_type max -max_paths 1]
if {$worst_path eq ""} { error "no routed max-delay timing path found" }
puts [format "SYMMETRIC HOLDOUT ROUTED WNS %.3f ns" \
    [get_property SLACK $worst_path]]
write_bitstream -force [file join $OUT system_holdout_symmetric.bit]
set hwh [glob -nocomplain \
    [file join $OUT proj *.gen sources_1 bd system hw_handoff system.hwh] \
    [file join $OUT proj *.srcs sources_1 bd system hw_handoff system.hwh]]
if {$hwh eq ""} { error "system.hwh was not generated" }
file copy -force [lindex $hwh 0] \
    [file join $OUT system_holdout_symmetric.hwh]
puts "SYMMETRIC HOLDOUT BITSTREAM DONE"
