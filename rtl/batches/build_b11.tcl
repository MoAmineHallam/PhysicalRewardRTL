# Auto-generated headless Vivado build  -  batch 11.
# ---- fill these in once for your board/project ----
set PART   "xc7z020clg400-1"        ;# PYNQ-Z2 part
set BD_TCL "$::env(HOME)/pynq_bd.tcl";# your block design (Zynq PS + AXI + la_axi) hook
# ---------------------------------------------------
set ROOT   "/home/user/FPGA"
set RTL_LIB "/home/user/FPGA/rtl_library"
set OUT    "$ROOT/rtl/batches/out_b11"
file mkdir $OUT

create_project -in_memory -part $PART
read_verilog $ROOT/rtl/la_axi.v
read_verilog $ROOT/rtl/batches/dut_top_b11.v
read_verilog $RTL_LIB/thresh5_30/design.v \
    $RTL_LIB/thresh6_32/design.v \
    $RTL_LIB/thresh6_48/design.v \
    $RTL_LIB/thresh6_16/design.v \
    $RTL_LIB/thresh6_62/design.v \
    $RTL_LIB/thresh7_64/design.v \
    $RTL_LIB/thresh7_96/design.v \
    $RTL_LIB/thresh7_32/design.v \
    $RTL_LIB/thresh7_126/design.v \
    $RTL_LIB/thresh8_128/design.v \
    $RTL_LIB/thresh8_192/design.v \
    $RTL_LIB/thresh8_64/design.v \
    $RTL_LIB/thresh8_254/design.v \
    $RTL_LIB/parity3/design.v \
    $RTL_LIB/popcount3/design.v \
    $RTL_LIB/reverse3/design.v \
    $RTL_LIB/gray3/design.v \
    $RTL_LIB/parity4/design.v \
    $RTL_LIB/popcount4/design.v \
    $RTL_LIB/reverse4/design.v \
    $RTL_LIB/gray4/design.v \
    $RTL_LIB/parity5/design.v \
    $RTL_LIB/popcount5/design.v \
    $RTL_LIB/reverse5/design.v \
    $RTL_LIB/gray5/design.v \
    $RTL_LIB/parity6/design.v \
    $RTL_LIB/popcount6/design.v \
    $RTL_LIB/reverse6/design.v \
    $RTL_LIB/gray6/design.v \
    $RTL_LIB/parity7/design.v \
    $RTL_LIB/popcount7/design.v \
    $RTL_LIB/reverse7/design.v \
    $RTL_LIB/gray7/design.v \
    $RTL_LIB/parity8/design.v \
    $RTL_LIB/popcount8/design.v \
    $RTL_LIB/reverse8/design.v \
    $RTL_LIB/gray8/design.v \
    $RTL_LIB/parity9/design.v \
    $RTL_LIB/popcount9/design.v \
    $RTL_LIB/reverse9/design.v \
    $RTL_LIB/gray9/design.v \
    $RTL_LIB/parity10/design.v \
    $RTL_LIB/popcount10/design.v \
    $RTL_LIB/reverse10/design.v \
    $RTL_LIB/gray10/design.v \
    $RTL_LIB/parity11/design.v \
    $RTL_LIB/popcount11/design.v \
    $RTL_LIB/reverse11/design.v \
    $RTL_LIB/gray11/design.v \
    $RTL_LIB/parity12/design.v \
    $RTL_LIB/popcount12/design.v \
    $RTL_LIB/reverse12/design.v \
    $RTL_LIB/gray12/design.v \
    $RTL_LIB/parity13/design.v \
    $RTL_LIB/popcount13/design.v \
    $RTL_LIB/reverse13/design.v \
    $RTL_LIB/gray13/design.v \
    $RTL_LIB/parity14/design.v \
    $RTL_LIB/popcount14/design.v \
    $RTL_LIB/reverse14/design.v \
    $RTL_LIB/gray14/design.v \
    $RTL_LIB/parity15/design.v \
    $RTL_LIB/popcount15/design.v \
    $RTL_LIB/reverse15/design.v
# Bring in the Zynq PS / AXI / la_axi block design + top wrapper:
if {[file exists $BD_TCL]} { source $BD_TCL }

# Top is your board wrapper that instantiates dut_top + la_axi + PS.
synth_design -top design_1_wrapper -part $PART
opt_design
place_design
route_design
write_bitstream -force $OUT/system_b11.bit
write_hw_platform -fixed -force $OUT/system_b11.xsa
puts "BATCH 11 DONE -> $OUT/system_b11.bit"
