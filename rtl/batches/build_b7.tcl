# Auto-generated headless Vivado build  -  batch 7.
# ---- fill these in once for your board/project ----
set PART   "xc7z020clg400-1"        ;# PYNQ-Z2 part
set BD_TCL "$::env(HOME)/pynq_bd.tcl";# your block design (Zynq PS + AXI + la_axi) hook
# ---------------------------------------------------
set ROOT   "/home/user/FPGA"
set RTL_LIB "/home/user/FPGA/rtl_library"
set OUT    "$ROOT/rtl/batches/out_b7"
file mkdir $OUT

create_project -in_memory -part $PART
read_verilog $ROOT/rtl/la_axi.v
read_verilog $ROOT/rtl/batches/dut_top_b7.v
read_verilog $RTL_LIB/mul2x2/design.v \
    $RTL_LIB/mul2x3/design.v \
    $RTL_LIB/mul2x4/design.v \
    $RTL_LIB/mul2x5/design.v \
    $RTL_LIB/mul2x6/design.v \
    $RTL_LIB/mul2x7/design.v \
    $RTL_LIB/mul2x8/design.v \
    $RTL_LIB/mul3x2/design.v \
    $RTL_LIB/mul3x3/design.v \
    $RTL_LIB/mul3x4/design.v \
    $RTL_LIB/mul3x5/design.v \
    $RTL_LIB/mul3x6/design.v \
    $RTL_LIB/mul3x7/design.v \
    $RTL_LIB/mul3x8/design.v \
    $RTL_LIB/mul4x2/design.v \
    $RTL_LIB/mul4x3/design.v \
    $RTL_LIB/mul4x4/design.v \
    $RTL_LIB/mul4x5/design.v \
    $RTL_LIB/mul4x6/design.v \
    $RTL_LIB/mul4x7/design.v \
    $RTL_LIB/mul4x8/design.v \
    $RTL_LIB/mul5x2/design.v \
    $RTL_LIB/mul5x3/design.v \
    $RTL_LIB/mul5x4/design.v \
    $RTL_LIB/mul5x5/design.v \
    $RTL_LIB/mul5x6/design.v \
    $RTL_LIB/mul5x7/design.v \
    $RTL_LIB/mul5x8/design.v \
    $RTL_LIB/mul6x2/design.v \
    $RTL_LIB/mul6x3/design.v \
    $RTL_LIB/mul6x4/design.v \
    $RTL_LIB/mul6x5/design.v \
    $RTL_LIB/mul6x6/design.v \
    $RTL_LIB/mul6x7/design.v \
    $RTL_LIB/mul6x8/design.v \
    $RTL_LIB/mul7x2/design.v \
    $RTL_LIB/mul7x3/design.v \
    $RTL_LIB/mul7x4/design.v \
    $RTL_LIB/mul7x5/design.v \
    $RTL_LIB/mul7x6/design.v \
    $RTL_LIB/mul7x7/design.v \
    $RTL_LIB/mul7x8/design.v \
    $RTL_LIB/mul8x2/design.v \
    $RTL_LIB/mul8x3/design.v \
    $RTL_LIB/mul8x4/design.v \
    $RTL_LIB/mul8x5/design.v \
    $RTL_LIB/mul8x6/design.v \
    $RTL_LIB/mul8x7/design.v \
    $RTL_LIB/smul2x2/design.v \
    $RTL_LIB/smul3x3/design.v \
    $RTL_LIB/smul4x4/design.v \
    $RTL_LIB/smul5x5/design.v \
    $RTL_LIB/smul6x6/design.v \
    $RTL_LIB/smul7x7/design.v \
    $RTL_LIB/add2b/design.v \
    $RTL_LIB/sub2b/design.v \
    $RTL_LIB/addsub2b/design.v \
    $RTL_LIB/add3b/design.v \
    $RTL_LIB/sub3b/design.v \
    $RTL_LIB/addsub3b/design.v \
    $RTL_LIB/add4b/design.v \
    $RTL_LIB/sub4b/design.v \
    $RTL_LIB/addsub4b/design.v \
    $RTL_LIB/add5b/design.v
# Bring in the Zynq PS / AXI / la_axi block design + top wrapper:
if {[file exists $BD_TCL]} { source $BD_TCL }

# Top is your board wrapper that instantiates dut_top + la_axi + PS.
synth_design -top design_1_wrapper -part $PART
opt_design
place_design
route_design
write_bitstream -force $OUT/system_b7.bit
write_hw_platform -fixed -force $OUT/system_b7.xsa
puts "BATCH 7 DONE -> $OUT/system_b7.bit"
