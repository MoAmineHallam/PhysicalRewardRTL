# Auto-generated headless Vivado build  -  batch 15.
# ---- fill these in once for your board/project ----
set PART   "xc7z020clg400-1"        ;# PYNQ-Z2 part
set BD_TCL "$::env(HOME)/pynq_bd.tcl";# your block design (Zynq PS + AXI + la_axi) hook
# ---------------------------------------------------
set ROOT   "/home/user/FPGA"
set RTL_LIB "/home/user/FPGA/rtl_library"
set OUT    "$ROOT/rtl/batches/out_b15"
file mkdir $OUT

create_project -in_memory -part $PART
read_verilog $ROOT/rtl/la_axi.v
read_verilog $ROOT/rtl/batches/dut_top_b15.v
read_verilog $RTL_LIB/acc8to8/design.v \
    $RTL_LIB/acc8to10/design.v \
    $RTL_LIB/acc8to12/design.v \
    $RTL_LIB/acc8to14/design.v \
    $RTL_LIB/acc8to16/design.v \
    $RTL_LIB/mac2_8b/design.v \
    $RTL_LIB/mac2_10b/design.v \
    $RTL_LIB/mac2_12b/design.v \
    $RTL_LIB/mac2_14b/design.v \
    $RTL_LIB/mac2_16b/design.v \
    $RTL_LIB/mac3_8b/design.v \
    $RTL_LIB/mac3_10b/design.v \
    $RTL_LIB/mac3_12b/design.v \
    $RTL_LIB/mac3_14b/design.v \
    $RTL_LIB/mac3_16b/design.v \
    $RTL_LIB/mac4_8b/design.v \
    $RTL_LIB/mac4_10b/design.v \
    $RTL_LIB/mac4_12b/design.v \
    $RTL_LIB/mac4_14b/design.v \
    $RTL_LIB/mac4_16b/design.v \
    $RTL_LIB/mac5_10b/design.v \
    $RTL_LIB/mac5_12b/design.v \
    $RTL_LIB/mac5_14b/design.v \
    $RTL_LIB/mac5_16b/design.v \
    $RTL_LIB/mac6_12b/design.v \
    $RTL_LIB/mac6_14b/design.v \
    $RTL_LIB/mac6_16b/design.v \
    $RTL_LIB/mac7_14b/design.v \
    $RTL_LIB/mac7_16b/design.v \
    $RTL_LIB/mac8_16b/design.v \
    $RTL_LIB/rmax4b/design.v \
    $RTL_LIB/rmin4b/design.v \
    $RTL_LIB/rmax5b/design.v \
    $RTL_LIB/rmin5b/design.v \
    $RTL_LIB/rmax6b/design.v \
    $RTL_LIB/rmin6b/design.v \
    $RTL_LIB/rmax7b/design.v \
    $RTL_LIB/rmin7b/design.v \
    $RTL_LIB/rmax8b/design.v \
    $RTL_LIB/rmin8b/design.v \
    $RTL_LIB/rmax10b/design.v \
    $RTL_LIB/rmin10b/design.v \
    $RTL_LIB/rmax12b/design.v \
    $RTL_LIB/rmin12b/design.v
# Bring in the Zynq PS / AXI / la_axi block design + top wrapper:
if {[file exists $BD_TCL]} { source $BD_TCL }

# Top is your board wrapper that instantiates dut_top + la_axi + PS.
synth_design -top design_1_wrapper -part $PART
opt_design
place_design
route_design
write_bitstream -force $OUT/system_b15.bit
write_hw_platform -fixed -force $OUT/system_b15.xsa
puts "BATCH 15 DONE -> $OUT/system_b15.bit"
