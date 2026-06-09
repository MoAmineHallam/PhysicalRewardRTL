# Auto-generated headless Vivado build  -  batch 9.
# ---- fill these in once for your board/project ----
set PART   "xc7z020clg400-1"        ;# PYNQ-Z2 part
set BD_TCL "$::env(HOME)/pynq_bd.tcl";# your block design (Zynq PS + AXI + la_axi) hook
# ---------------------------------------------------
set ROOT   "/home/user/FPGA"
set RTL_LIB "/home/user/FPGA/rtl_library"
set OUT    "$ROOT/rtl/batches/out_b9"
file mkdir $OUT

create_project -in_memory -part $PART
read_verilog $ROOT/rtl/la_axi.v
read_verilog $ROOT/rtl/batches/dut_top_b9.v
read_verilog $RTL_LIB/rotate_lsh16/design.v \
    $RTL_LIB/logical_rsh16/design.v \
    $RTL_LIB/rotate_rsh16/design.v \
    $RTL_LIB/rotl4_1/design.v \
    $RTL_LIB/rotl4_2/design.v \
    $RTL_LIB/rotl4_3/design.v \
    $RTL_LIB/rotl6_1/design.v \
    $RTL_LIB/rotl6_2/design.v \
    $RTL_LIB/rotl6_3/design.v \
    $RTL_LIB/rotl6_5/design.v \
    $RTL_LIB/rotl8_1/design.v \
    $RTL_LIB/rotl8_2/design.v \
    $RTL_LIB/rotl8_3/design.v \
    $RTL_LIB/rotl8_4/design.v \
    $RTL_LIB/rotl8_7/design.v \
    $RTL_LIB/rotl10_1/design.v \
    $RTL_LIB/rotl10_2/design.v \
    $RTL_LIB/rotl10_3/design.v \
    $RTL_LIB/rotl10_5/design.v \
    $RTL_LIB/rotl10_9/design.v \
    $RTL_LIB/rotl12_1/design.v \
    $RTL_LIB/rotl12_2/design.v \
    $RTL_LIB/rotl12_3/design.v \
    $RTL_LIB/rotl12_6/design.v \
    $RTL_LIB/rotl12_11/design.v \
    $RTL_LIB/rotl16_1/design.v \
    $RTL_LIB/rotl16_2/design.v \
    $RTL_LIB/rotl16_3/design.v \
    $RTL_LIB/rotl16_4/design.v \
    $RTL_LIB/rotl16_8/design.v \
    $RTL_LIB/rotl16_15/design.v \
    $RTL_LIB/cmp2b/design.v \
    $RTL_LIB/cmp3b/design.v \
    $RTL_LIB/cmp4b/design.v \
    $RTL_LIB/cmp5b/design.v \
    $RTL_LIB/cmp6b/design.v \
    $RTL_LIB/cmp7b/design.v \
    $RTL_LIB/cmp8b/design.v \
    $RTL_LIB/cmp9b/design.v \
    $RTL_LIB/cmp10b/design.v \
    $RTL_LIB/cmp11b/design.v \
    $RTL_LIB/cmp12b/design.v \
    $RTL_LIB/cmp13b/design.v \
    $RTL_LIB/cmp14b/design.v \
    $RTL_LIB/cmp15b/design.v \
    $RTL_LIB/cmp16b/design.v \
    $RTL_LIB/min2b/design.v \
    $RTL_LIB/max2b/design.v \
    $RTL_LIB/min3b/design.v \
    $RTL_LIB/max3b/design.v \
    $RTL_LIB/min4b/design.v \
    $RTL_LIB/max4b/design.v \
    $RTL_LIB/min5b/design.v \
    $RTL_LIB/max5b/design.v \
    $RTL_LIB/min6b/design.v \
    $RTL_LIB/max6b/design.v \
    $RTL_LIB/min7b/design.v \
    $RTL_LIB/max7b/design.v \
    $RTL_LIB/min8b/design.v \
    $RTL_LIB/max8b/design.v \
    $RTL_LIB/min9b/design.v \
    $RTL_LIB/max9b/design.v \
    $RTL_LIB/min10b/design.v \
    $RTL_LIB/max10b/design.v
# Bring in the Zynq PS / AXI / la_axi block design + top wrapper:
if {[file exists $BD_TCL]} { source $BD_TCL }

# Top is your board wrapper that instantiates dut_top + la_axi + PS.
synth_design -top design_1_wrapper -part $PART
opt_design
place_design
route_design
write_bitstream -force $OUT/system_b9.bit
write_hw_platform -fixed -force $OUT/system_b9.xsa
puts "BATCH 9 DONE -> $OUT/system_b9.bit"
