# Auto-generated headless Vivado build  -  batch 10.
# ---- fill these in once for your board/project ----
set PART   "xc7z020clg400-1"        ;# PYNQ-Z2 part
set BD_TCL "$::env(HOME)/pynq_bd.tcl";# your block design (Zynq PS + AXI + la_axi) hook
# ---------------------------------------------------
set ROOT   "/home/user/FPGA"
set RTL_LIB "/home/user/FPGA/rtl_library"
set OUT    "$ROOT/rtl/batches/out_b10"
file mkdir $OUT

create_project -in_memory -part $PART
read_verilog $ROOT/rtl/la_axi.v
read_verilog $ROOT/rtl/batches/dut_top_b10.v
read_verilog $RTL_LIB/min11b/design.v \
    $RTL_LIB/max11b/design.v \
    $RTL_LIB/min12b/design.v \
    $RTL_LIB/max12b/design.v \
    $RTL_LIB/min13b/design.v \
    $RTL_LIB/max13b/design.v \
    $RTL_LIB/min14b/design.v \
    $RTL_LIB/max14b/design.v \
    $RTL_LIB/min15b/design.v \
    $RTL_LIB/max15b/design.v \
    $RTL_LIB/min16b/design.v \
    $RTL_LIB/max16b/design.v \
    $RTL_LIB/window4_4_12/design.v \
    $RTL_LIB/window4_1_8/design.v \
    $RTL_LIB/window4_5_10/design.v \
    $RTL_LIB/window4_2_8/design.v \
    $RTL_LIB/window4_4_15/design.v \
    $RTL_LIB/window5_8_24/design.v \
    $RTL_LIB/window5_1_16/design.v \
    $RTL_LIB/window5_10_21/design.v \
    $RTL_LIB/window5_4_16/design.v \
    $RTL_LIB/window5_8_31/design.v \
    $RTL_LIB/window6_16_48/design.v \
    $RTL_LIB/window6_1_32/design.v \
    $RTL_LIB/window6_21_42/design.v \
    $RTL_LIB/window6_8_32/design.v \
    $RTL_LIB/window6_16_63/design.v \
    $RTL_LIB/window7_32_96/design.v \
    $RTL_LIB/window7_1_64/design.v \
    $RTL_LIB/window7_42_85/design.v \
    $RTL_LIB/window7_16_64/design.v \
    $RTL_LIB/window7_32_127/design.v \
    $RTL_LIB/window8_64_192/design.v \
    $RTL_LIB/window8_1_128/design.v \
    $RTL_LIB/window8_85_170/design.v \
    $RTL_LIB/window8_32_128/design.v \
    $RTL_LIB/window8_64_255/design.v \
    $RTL_LIB/clamp4_12/design.v \
    $RTL_LIB/clamp4_9/design.v \
    $RTL_LIB/clamp4_8/design.v \
    $RTL_LIB/clamp4_14/design.v \
    $RTL_LIB/clamp5_24/design.v \
    $RTL_LIB/clamp5_17/design.v \
    $RTL_LIB/clamp5_16/design.v \
    $RTL_LIB/clamp5_30/design.v \
    $RTL_LIB/clamp6_48/design.v \
    $RTL_LIB/clamp6_33/design.v \
    $RTL_LIB/clamp6_32/design.v \
    $RTL_LIB/clamp6_62/design.v \
    $RTL_LIB/clamp7_96/design.v \
    $RTL_LIB/clamp7_65/design.v \
    $RTL_LIB/clamp7_64/design.v \
    $RTL_LIB/clamp7_126/design.v \
    $RTL_LIB/clamp8_192/design.v \
    $RTL_LIB/clamp8_129/design.v \
    $RTL_LIB/clamp8_128/design.v \
    $RTL_LIB/clamp8_254/design.v \
    $RTL_LIB/thresh4_8/design.v \
    $RTL_LIB/thresh4_12/design.v \
    $RTL_LIB/thresh4_4/design.v \
    $RTL_LIB/thresh4_14/design.v \
    $RTL_LIB/thresh5_16/design.v \
    $RTL_LIB/thresh5_24/design.v \
    $RTL_LIB/thresh5_8/design.v
# Bring in the Zynq PS / AXI / la_axi block design + top wrapper:
if {[file exists $BD_TCL]} { source $BD_TCL }

# Top is your board wrapper that instantiates dut_top + la_axi + PS.
synth_design -top design_1_wrapper -part $PART
opt_design
place_design
route_design
write_bitstream -force $OUT/system_b10.bit
write_hw_platform -fixed -force $OUT/system_b10.xsa
puts "BATCH 10 DONE -> $OUT/system_b10.bit"
