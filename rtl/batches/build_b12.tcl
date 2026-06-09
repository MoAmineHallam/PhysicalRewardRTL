# Auto-generated headless Vivado build  -  batch 12.
# ---- fill these in once for your board/project ----
set PART   "xc7z020clg400-1"        ;# PYNQ-Z2 part
set BD_TCL "$::env(HOME)/pynq_bd.tcl";# your block design (Zynq PS + AXI + la_axi) hook
# ---------------------------------------------------
set ROOT   "/home/user/FPGA"
set RTL_LIB "/home/user/FPGA/rtl_library"
set OUT    "$ROOT/rtl/batches/out_b12"
file mkdir $OUT

create_project -in_memory -part $PART
read_verilog $ROOT/rtl/la_axi.v
read_verilog $ROOT/rtl/batches/dut_top_b12.v
read_verilog $RTL_LIB/gray15/design.v \
    $RTL_LIB/parity16/design.v \
    $RTL_LIB/popcount16/design.v \
    $RTL_LIB/reverse16/design.v \
    $RTL_LIB/gray16/design.v \
    $RTL_LIB/neg_twos3b/design.v \
    $RTL_LIB/neg_ones3b/design.v \
    $RTL_LIB/neg_twos4b/design.v \
    $RTL_LIB/neg_ones4b/design.v \
    $RTL_LIB/neg_twos5b/design.v \
    $RTL_LIB/neg_ones5b/design.v \
    $RTL_LIB/neg_twos6b/design.v \
    $RTL_LIB/neg_ones6b/design.v \
    $RTL_LIB/neg_twos7b/design.v \
    $RTL_LIB/neg_ones7b/design.v \
    $RTL_LIB/neg_twos8b/design.v \
    $RTL_LIB/neg_ones8b/design.v \
    $RTL_LIB/neg_twos9b/design.v \
    $RTL_LIB/neg_ones9b/design.v \
    $RTL_LIB/neg_twos10b/design.v \
    $RTL_LIB/neg_ones10b/design.v \
    $RTL_LIB/neg_twos11b/design.v \
    $RTL_LIB/neg_ones11b/design.v \
    $RTL_LIB/neg_twos12b/design.v \
    $RTL_LIB/neg_ones12b/design.v \
    $RTL_LIB/neg_twos13b/design.v \
    $RTL_LIB/neg_ones13b/design.v \
    $RTL_LIB/neg_twos14b/design.v \
    $RTL_LIB/neg_ones14b/design.v \
    $RTL_LIB/neg_twos15b/design.v \
    $RTL_LIB/neg_ones15b/design.v \
    $RTL_LIB/neg_twos16b/design.v \
    $RTL_LIB/neg_ones16b/design.v \
    $RTL_LIB/abs3b/design.v \
    $RTL_LIB/abs4b/design.v \
    $RTL_LIB/abs5b/design.v \
    $RTL_LIB/abs6b/design.v \
    $RTL_LIB/abs7b/design.v \
    $RTL_LIB/abs8b/design.v \
    $RTL_LIB/abs9b/design.v \
    $RTL_LIB/abs10b/design.v \
    $RTL_LIB/abs11b/design.v \
    $RTL_LIB/abs12b/design.v \
    $RTL_LIB/halfswap4/design.v \
    $RTL_LIB/halfswap6/design.v \
    $RTL_LIB/halfswap8/design.v \
    $RTL_LIB/halfswap10/design.v \
    $RTL_LIB/halfswap12/design.v \
    $RTL_LIB/halfswap14/design.v \
    $RTL_LIB/halfswap16/design.v \
    $RTL_LIB/prienc2/design.v \
    $RTL_LIB/prienc3/design.v \
    $RTL_LIB/prienc4/design.v \
    $RTL_LIB/prienc5/design.v \
    $RTL_LIB/prienc6/design.v \
    $RTL_LIB/prienc7/design.v \
    $RTL_LIB/prienc8/design.v \
    $RTL_LIB/prienc9/design.v \
    $RTL_LIB/prienc10/design.v \
    $RTL_LIB/prienc11/design.v \
    $RTL_LIB/prienc12/design.v \
    $RTL_LIB/prienc13/design.v \
    $RTL_LIB/prienc14/design.v \
    $RTL_LIB/prienc15/design.v
# Bring in the Zynq PS / AXI / la_axi block design + top wrapper:
if {[file exists $BD_TCL]} { source $BD_TCL }

# Top is your board wrapper that instantiates dut_top + la_axi + PS.
synth_design -top design_1_wrapper -part $PART
opt_design
place_design
route_design
write_bitstream -force $OUT/system_b12.bit
write_hw_platform -fixed -force $OUT/system_b12.xsa
puts "BATCH 12 DONE -> $OUT/system_b12.bit"
