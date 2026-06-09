# Auto-generated headless Vivado build  -  batch 13.
# ---- fill these in once for your board/project ----
set PART   "xc7z020clg400-1"        ;# PYNQ-Z2 part
set BD_TCL "$::env(HOME)/pynq_bd.tcl";# your block design (Zynq PS + AXI + la_axi) hook
# ---------------------------------------------------
set ROOT   "/home/user/FPGA"
set RTL_LIB "/home/user/FPGA/rtl_library"
set OUT    "$ROOT/rtl/batches/out_b13"
file mkdir $OUT

create_project -in_memory -part $PART
read_verilog $ROOT/rtl/la_axi.v
read_verilog $ROOT/rtl/batches/dut_top_b13.v
read_verilog $RTL_LIB/prienc16/design.v \
    $RTL_LIB/decoder2to4/design.v \
    $RTL_LIB/decoder3to8/design.v \
    $RTL_LIB/decoder4to16/design.v \
    $RTL_LIB/mux2x1b/design.v \
    $RTL_LIB/mux2x2b/design.v \
    $RTL_LIB/mux2x3b/design.v \
    $RTL_LIB/mux2x4b/design.v \
    $RTL_LIB/mux4x1b/design.v \
    $RTL_LIB/mux4x2b/design.v \
    $RTL_LIB/mux4x3b/design.v \
    $RTL_LIB/mux4x4b/design.v \
    $RTL_LIB/mux8x1b/design.v \
    $RTL_LIB/mux8x2b/design.v \
    $RTL_LIB/mux8x3b/design.v \
    $RTL_LIB/mux16x1b/design.v \
    $RTL_LIB/demux1to2/design.v \
    $RTL_LIB/demux1to4/design.v \
    $RTL_LIB/demux1to8/design.v \
    $RTL_LIB/demux1to16/design.v \
    $RTL_LIB/gray2bin3/design.v \
    $RTL_LIB/gray2bin4/design.v \
    $RTL_LIB/gray2bin5/design.v \
    $RTL_LIB/gray2bin6/design.v \
    $RTL_LIB/gray2bin7/design.v \
    $RTL_LIB/gray2bin8/design.v \
    $RTL_LIB/gray2bin9/design.v \
    $RTL_LIB/gray2bin10/design.v \
    $RTL_LIB/gray2bin11/design.v \
    $RTL_LIB/gray2bin12/design.v \
    $RTL_LIB/gray2bin13/design.v \
    $RTL_LIB/gray2bin14/design.v \
    $RTL_LIB/gray2bin15/design.v \
    $RTL_LIB/gray2bin16/design.v \
    $RTL_LIB/alu4_2op/design.v \
    $RTL_LIB/alu4_3op/design.v \
    $RTL_LIB/alu4_4op/design.v \
    $RTL_LIB/alu4_5op/design.v \
    $RTL_LIB/alu4_6op/design.v \
    $RTL_LIB/alu4_7op/design.v \
    $RTL_LIB/alu4_8op/design.v \
    $RTL_LIB/alu5_2op/design.v \
    $RTL_LIB/alu5_3op/design.v \
    $RTL_LIB/alu5_4op/design.v \
    $RTL_LIB/alu5_5op/design.v \
    $RTL_LIB/alu5_6op/design.v \
    $RTL_LIB/alu5_7op/design.v \
    $RTL_LIB/alu5_8op/design.v \
    $RTL_LIB/alu6_2op/design.v \
    $RTL_LIB/alu6_3op/design.v \
    $RTL_LIB/alu6_4op/design.v \
    $RTL_LIB/alu6_5op/design.v \
    $RTL_LIB/alu6_6op/design.v \
    $RTL_LIB/alu6_7op/design.v \
    $RTL_LIB/alu6_8op/design.v \
    $RTL_LIB/alu7_2op/design.v \
    $RTL_LIB/alu7_3op/design.v \
    $RTL_LIB/alu7_4op/design.v \
    $RTL_LIB/alu7_5op/design.v \
    $RTL_LIB/alu7_6op/design.v \
    $RTL_LIB/alu7_7op/design.v \
    $RTL_LIB/alu7_8op/design.v \
    $RTL_LIB/alu8_2op/design.v \
    $RTL_LIB/alu8_3op/design.v
# Bring in the Zynq PS / AXI / la_axi block design + top wrapper:
if {[file exists $BD_TCL]} { source $BD_TCL }

# Top is your board wrapper that instantiates dut_top + la_axi + PS.
synth_design -top design_1_wrapper -part $PART
opt_design
place_design
route_design
write_bitstream -force $OUT/system_b13.bit
write_hw_platform -fixed -force $OUT/system_b13.xsa
puts "BATCH 13 DONE -> $OUT/system_b13.bit"
