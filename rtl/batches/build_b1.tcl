# Auto-generated headless Vivado build  -  batch 1.
# ---- fill these in once for your board/project ----
set PART   "xc7z020clg400-1"        ;# PYNQ-Z2 part
set BD_TCL "$::env(HOME)/pynq_bd.tcl";# your block design (Zynq PS + AXI + la_axi) hook
# ---------------------------------------------------
set ROOT   "/home/user/FPGA"
set RTL_LIB "/home/user/FPGA/rtl_library"
set OUT    "$ROOT/rtl/batches/out_b1"
file mkdir $OUT

create_project -in_memory -part $PART
read_verilog $ROOT/rtl/la_axi.v
read_verilog $ROOT/rtl/batches/dut_top_b1.v
read_verilog $RTL_LIB/mod42_counter/design.v \
    $RTL_LIB/mod43_counter/design.v \
    $RTL_LIB/mod44_counter/design.v \
    $RTL_LIB/mod45_counter/design.v \
    $RTL_LIB/mod46_counter/design.v \
    $RTL_LIB/mod47_counter/design.v \
    $RTL_LIB/mod48_counter/design.v \
    $RTL_LIB/mod49_counter/design.v \
    $RTL_LIB/mod50_counter/design.v \
    $RTL_LIB/mod51_counter/design.v \
    $RTL_LIB/mod52_counter/design.v \
    $RTL_LIB/mod53_counter/design.v \
    $RTL_LIB/mod54_counter/design.v \
    $RTL_LIB/mod55_counter/design.v \
    $RTL_LIB/mod56_counter/design.v \
    $RTL_LIB/mod57_counter/design.v \
    $RTL_LIB/mod58_counter/design.v \
    $RTL_LIB/mod59_counter/design.v \
    $RTL_LIB/mod60_counter/design.v \
    $RTL_LIB/mod61_counter/design.v \
    $RTL_LIB/mod62_counter/design.v \
    $RTL_LIB/mod63_counter/design.v \
    $RTL_LIB/mod64_counter/design.v \
    $RTL_LIB/mod65_counter/design.v \
    $RTL_LIB/mod66_counter/design.v \
    $RTL_LIB/mod67_counter/design.v \
    $RTL_LIB/mod68_counter/design.v \
    $RTL_LIB/mod69_counter/design.v \
    $RTL_LIB/mod70_counter/design.v \
    $RTL_LIB/mod71_counter/design.v \
    $RTL_LIB/mod72_counter/design.v \
    $RTL_LIB/mod73_counter/design.v \
    $RTL_LIB/mod74_counter/design.v \
    $RTL_LIB/mod75_counter/design.v \
    $RTL_LIB/mod76_counter/design.v \
    $RTL_LIB/mod77_counter/design.v \
    $RTL_LIB/mod78_counter/design.v \
    $RTL_LIB/mod79_counter/design.v \
    $RTL_LIB/mod80_counter/design.v \
    $RTL_LIB/mod81_counter/design.v \
    $RTL_LIB/mod82_counter/design.v \
    $RTL_LIB/mod83_counter/design.v \
    $RTL_LIB/mod84_counter/design.v \
    $RTL_LIB/mod85_counter/design.v \
    $RTL_LIB/mod86_counter/design.v \
    $RTL_LIB/mod87_counter/design.v \
    $RTL_LIB/mod88_counter/design.v \
    $RTL_LIB/mod89_counter/design.v \
    $RTL_LIB/mod90_counter/design.v \
    $RTL_LIB/mod91_counter/design.v \
    $RTL_LIB/mod92_counter/design.v \
    $RTL_LIB/mod93_counter/design.v \
    $RTL_LIB/mod94_counter/design.v \
    $RTL_LIB/mod95_counter/design.v \
    $RTL_LIB/mod96_counter/design.v \
    $RTL_LIB/mod98_counter/design.v \
    $RTL_LIB/mod100_counter/design.v \
    $RTL_LIB/mod102_counter/design.v \
    $RTL_LIB/mod104_counter/design.v \
    $RTL_LIB/mod106_counter/design.v \
    $RTL_LIB/mod108_counter/design.v \
    $RTL_LIB/mod110_counter/design.v \
    $RTL_LIB/mod112_counter/design.v \
    $RTL_LIB/mod114_counter/design.v
# Bring in the Zynq PS / AXI / la_axi block design + top wrapper:
if {[file exists $BD_TCL]} { source $BD_TCL }

# Top is your board wrapper that instantiates dut_top + la_axi + PS.
synth_design -top design_1_wrapper -part $PART
opt_design
place_design
route_design
write_bitstream -force $OUT/system_b1.bit
write_hw_platform -fixed -force $OUT/system_b1.xsa
puts "BATCH 1 DONE -> $OUT/system_b1.bit"
