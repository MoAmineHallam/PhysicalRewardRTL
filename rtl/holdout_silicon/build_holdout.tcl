# Auto-generated - Phase C held-out silicon money-table bitstream.
set PART    "xc7z020clg400-1"
set CLK_MHZ 200
set ROOT    [file normalize [file join [file dirname [info script]] .. ..]]
set OUT     [file join $ROOT rtl holdout_silicon out]
file mkdir $OUT

create_project sys_holdout [file join $OUT proj] -part $PART -force
add_files [list \
    [file join $ROOT rtl la_axi_fast.v] \
    [file join $ROOT rtl holdout_silicon dut_top_holdout.v] \
    [file join $ROOT rtl_library echo8b design.v] \
    [file join $ROOT rtl holdout_silicon duts sft__fir26_8b__g1.v] \
    [file join $ROOT rtl holdout_silicon duts grpo__fir26_8b__g0.v] \
    [file join $ROOT rtl holdout_silicon duts sft__firr26__g0.v] \
    [file join $ROOT rtl holdout_silicon duts grpo__firr26__g0.v] \
    [file join $ROOT rtl holdout_silicon duts sft__poly7_8b__g1.v] \
    [file join $ROOT rtl holdout_silicon duts grpo__poly7_8b__g0.v] \
    [file join $ROOT rtl holdout_silicon duts sft__firr36__g0.v] \
    [file join $ROOT rtl holdout_silicon duts grpo__firr36__g0.v] \
    [file join $ROOT rtl holdout_silicon duts sft__poly8_v6_8b__g1.v] \
    [file join $ROOT rtl holdout_silicon duts grpo__poly8_v6_8b__g0.v] ]
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

make_wrapper -files [get_files system.bd] -top -force
add_files -norecurse [glob \
    [file join $OUT proj *.gen sources_1 bd system hdl system_wrapper.v] \
    [file join $OUT proj *.srcs sources_1 bd system hdl system_wrapper.v]]
set_property top system_wrapper [current_fileset]

launch_runs synth_1 -jobs 8
wait_on_run synth_1
launch_runs impl_1 -to_step write_bitstream -jobs 8
wait_on_run impl_1
file copy -force [glob [file join $OUT proj *.runs impl_1 system_wrapper.bit]] \
    [file join $OUT system_holdout.bit]
set hwh [glob -nocomplain \
    [file join $OUT proj *.gen sources_1 bd system hw_handoff system.hwh] \
    [file join $OUT proj *.srcs sources_1 bd system hw_handoff system.hwh]]
if {$hwh ne ""} {
    file copy -force [lindex $hwh 0] [file join $OUT system_holdout.hwh]
}
puts "HOLDOUT BITSTREAM DONE"
