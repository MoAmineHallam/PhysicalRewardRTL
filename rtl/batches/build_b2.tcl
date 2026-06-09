# Auto-generated headless Vivado build  -  batch 2.
# ---- fill these in once for your board/project ----
set PART   "xc7z020clg400-1"        ;# PYNQ-Z2 part
set BD_TCL "$::env(HOME)/pynq_bd.tcl";# your block design (Zynq PS + AXI + la_axi) hook
# ---------------------------------------------------
set ROOT   "/home/user/FPGA"
set RTL_LIB "/home/user/FPGA/rtl_library"
set OUT    "$ROOT/rtl/batches/out_b2"
file mkdir $OUT

create_project -in_memory -part $PART
read_verilog $ROOT/rtl/la_axi.v
read_verilog $ROOT/rtl/batches/dut_top_b2.v
read_verilog $RTL_LIB/mod116_counter/design.v \
    $RTL_LIB/mod118_counter/design.v \
    $RTL_LIB/mod120_counter/design.v \
    $RTL_LIB/mod122_counter/design.v \
    $RTL_LIB/mod124_counter/design.v \
    $RTL_LIB/mod126_counter/design.v \
    $RTL_LIB/mod128_counter/design.v \
    $RTL_LIB/mod130_counter/design.v \
    $RTL_LIB/mod132_counter/design.v \
    $RTL_LIB/mod134_counter/design.v \
    $RTL_LIB/mod136_counter/design.v \
    $RTL_LIB/mod138_counter/design.v \
    $RTL_LIB/mod140_counter/design.v \
    $RTL_LIB/mod142_counter/design.v \
    $RTL_LIB/mod144_counter/design.v \
    $RTL_LIB/mod146_counter/design.v \
    $RTL_LIB/mod148_counter/design.v \
    $RTL_LIB/mod150_counter/design.v \
    $RTL_LIB/mod152_counter/design.v \
    $RTL_LIB/mod154_counter/design.v \
    $RTL_LIB/mod156_counter/design.v \
    $RTL_LIB/mod158_counter/design.v \
    $RTL_LIB/mod160_counter/design.v \
    $RTL_LIB/mod162_counter/design.v \
    $RTL_LIB/mod164_counter/design.v \
    $RTL_LIB/mod166_counter/design.v \
    $RTL_LIB/mod168_counter/design.v \
    $RTL_LIB/mod170_counter/design.v \
    $RTL_LIB/mod172_counter/design.v \
    $RTL_LIB/mod174_counter/design.v \
    $RTL_LIB/mod176_counter/design.v \
    $RTL_LIB/mod178_counter/design.v \
    $RTL_LIB/mod180_counter/design.v \
    $RTL_LIB/mod182_counter/design.v \
    $RTL_LIB/mod184_counter/design.v \
    $RTL_LIB/mod186_counter/design.v \
    $RTL_LIB/mod188_counter/design.v \
    $RTL_LIB/mod190_counter/design.v \
    $RTL_LIB/mod192_counter/design.v \
    $RTL_LIB/mod194_counter/design.v \
    $RTL_LIB/mod196_counter/design.v \
    $RTL_LIB/mod198_counter/design.v \
    $RTL_LIB/mod208_counter/design.v \
    $RTL_LIB/mod224_counter/design.v \
    $RTL_LIB/mod240_counter/design.v \
    $RTL_LIB/mod250_counter/design.v \
    $RTL_LIB/mod256_counter/design.v \
    $RTL_LIB/counter2b/design.v \
    $RTL_LIB/counter3b/design.v \
    $RTL_LIB/counter4b/design.v \
    $RTL_LIB/counter5b/design.v \
    $RTL_LIB/counter6b/design.v \
    $RTL_LIB/counter7b/design.v \
    $RTL_LIB/counter8b/design.v \
    $RTL_LIB/counter9b/design.v \
    $RTL_LIB/counter10b/design.v \
    $RTL_LIB/counter11b/design.v \
    $RTL_LIB/counter12b/design.v \
    $RTL_LIB/counter13b/design.v \
    $RTL_LIB/counter14b/design.v \
    $RTL_LIB/counter15b/design.v \
    $RTL_LIB/counter16b/design.v \
    $RTL_LIB/updown3b/design.v \
    $RTL_LIB/updown4b/design.v
# Bring in the Zynq PS / AXI / la_axi block design + top wrapper:
if {[file exists $BD_TCL]} { source $BD_TCL }

# Top is your board wrapper that instantiates dut_top + la_axi + PS.
synth_design -top design_1_wrapper -part $PART
opt_design
place_design
route_design
write_bitstream -force $OUT/system_b2.bit
write_hw_platform -fixed -force $OUT/system_b2.xsa
puts "BATCH 2 DONE -> $OUT/system_b2.bit"
