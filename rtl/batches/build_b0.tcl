# Auto-generated headless Vivado build  -  batch 0.
# ---- fill these in once for your board/project ----
set PART   "xc7z020clg400-1"        ;# PYNQ-Z2 part
set BD_TCL "$::env(HOME)/pynq_bd.tcl";# your block design (Zynq PS + AXI + la_axi) hook
# ---------------------------------------------------
set ROOT   "/home/user/FPGA"
set RTL_LIB "/home/user/FPGA/rtl_library"
set OUT    "$ROOT/rtl/batches/out_b0"
file mkdir $OUT

create_project -in_memory -part $PART
read_verilog $ROOT/rtl/la_axi.v
read_verilog $ROOT/rtl/batches/dut_top_b0.v
read_verilog $RTL_LIB/bitand2b/design.v \
    $RTL_LIB/bitor2b/design.v \
    $RTL_LIB/bitxor2b/design.v \
    $RTL_LIB/bitnand2b/design.v \
    $RTL_LIB/bitnor2b/design.v \
    $RTL_LIB/bitxnor2b/design.v \
    $RTL_LIB/bitand4b/design.v \
    $RTL_LIB/bitor4b/design.v \
    $RTL_LIB/bitxor4b/design.v \
    $RTL_LIB/bitnand4b/design.v \
    $RTL_LIB/bitnor4b/design.v \
    $RTL_LIB/bitxnor4b/design.v \
    $RTL_LIB/bitand6b/design.v \
    $RTL_LIB/bitor6b/design.v \
    $RTL_LIB/bitxor6b/design.v \
    $RTL_LIB/bitnand6b/design.v \
    $RTL_LIB/bitnor6b/design.v \
    $RTL_LIB/bitxnor6b/design.v \
    $RTL_LIB/bitand8b/design.v \
    $RTL_LIB/bitor8b/design.v \
    $RTL_LIB/bitxor8b/design.v \
    $RTL_LIB/bitnand8b/design.v \
    $RTL_LIB/bitnor8b/design.v \
    $RTL_LIB/bitxnor8b/design.v \
    $RTL_LIB/mod2_counter/design.v \
    $RTL_LIB/mod3_counter/design.v \
    $RTL_LIB/mod4_counter/design.v \
    $RTL_LIB/mod5_counter/design.v \
    $RTL_LIB/mod6_counter/design.v \
    $RTL_LIB/mod7_counter/design.v \
    $RTL_LIB/mod8_counter/design.v \
    $RTL_LIB/mod9_counter/design.v \
    $RTL_LIB/mod10_counter/design.v \
    $RTL_LIB/mod11_counter/design.v \
    $RTL_LIB/mod12_counter/design.v \
    $RTL_LIB/mod13_counter/design.v \
    $RTL_LIB/mod14_counter/design.v \
    $RTL_LIB/mod15_counter/design.v \
    $RTL_LIB/mod16_counter/design.v \
    $RTL_LIB/mod17_counter/design.v \
    $RTL_LIB/mod18_counter/design.v \
    $RTL_LIB/mod19_counter/design.v \
    $RTL_LIB/mod20_counter/design.v \
    $RTL_LIB/mod21_counter/design.v \
    $RTL_LIB/mod22_counter/design.v \
    $RTL_LIB/mod23_counter/design.v \
    $RTL_LIB/mod24_counter/design.v \
    $RTL_LIB/mod25_counter/design.v \
    $RTL_LIB/mod26_counter/design.v \
    $RTL_LIB/mod27_counter/design.v \
    $RTL_LIB/mod28_counter/design.v \
    $RTL_LIB/mod29_counter/design.v \
    $RTL_LIB/mod30_counter/design.v \
    $RTL_LIB/mod31_counter/design.v \
    $RTL_LIB/mod32_counter/design.v \
    $RTL_LIB/mod33_counter/design.v \
    $RTL_LIB/mod34_counter/design.v \
    $RTL_LIB/mod35_counter/design.v \
    $RTL_LIB/mod36_counter/design.v \
    $RTL_LIB/mod37_counter/design.v \
    $RTL_LIB/mod38_counter/design.v \
    $RTL_LIB/mod39_counter/design.v \
    $RTL_LIB/mod40_counter/design.v \
    $RTL_LIB/mod41_counter/design.v
# Bring in the Zynq PS / AXI / la_axi block design + top wrapper:
if {[file exists $BD_TCL]} { source $BD_TCL }

# Top is your board wrapper that instantiates dut_top + la_axi + PS.
synth_design -top design_1_wrapper -part $PART
opt_design
place_design
route_design
write_bitstream -force $OUT/system_b0.bit
write_hw_platform -fixed -force $OUT/system_b0.xsa
puts "BATCH 0 DONE -> $OUT/system_b0.bit"
