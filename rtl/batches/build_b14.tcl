# Auto-generated headless Vivado build  -  batch 14.
# ---- fill these in once for your board/project ----
set PART   "xc7z020clg400-1"        ;# PYNQ-Z2 part
set BD_TCL "$::env(HOME)/pynq_bd.tcl";# your block design (Zynq PS + AXI + la_axi) hook
# ---------------------------------------------------
set ROOT   "/home/user/FPGA"
set RTL_LIB "/home/user/FPGA/rtl_library"
set OUT    "$ROOT/rtl/batches/out_b14"
file mkdir $OUT

create_project -in_memory -part $PART
read_verilog $ROOT/rtl/la_axi.v
read_verilog $ROOT/rtl/batches/dut_top_b14.v
read_verilog $RTL_LIB/alu8_4op/design.v \
    $RTL_LIB/alu8_5op/design.v \
    $RTL_LIB/alu8_6op/design.v \
    $RTL_LIB/alu8_7op/design.v \
    $RTL_LIB/alu8_8op/design.v \
    $RTL_LIB/alu10_2op/design.v \
    $RTL_LIB/alu10_3op/design.v \
    $RTL_LIB/alu10_4op/design.v \
    $RTL_LIB/alu10_5op/design.v \
    $RTL_LIB/alu10_6op/design.v \
    $RTL_LIB/alu10_7op/design.v \
    $RTL_LIB/alu10_8op/design.v \
    $RTL_LIB/alu12_2op/design.v \
    $RTL_LIB/alu12_3op/design.v \
    $RTL_LIB/alu12_4op/design.v \
    $RTL_LIB/alu12_5op/design.v \
    $RTL_LIB/alu12_6op/design.v \
    $RTL_LIB/alu12_7op/design.v \
    $RTL_LIB/alu12_8op/design.v \
    $RTL_LIB/lfsr4_0/design.v \
    $RTL_LIB/lfsr5_1/design.v \
    $RTL_LIB/lfsr6_2/design.v \
    $RTL_LIB/lfsr7_3/design.v \
    $RTL_LIB/lfsr8_4/design.v \
    $RTL_LIB/lfsr8_5/design.v \
    $RTL_LIB/lfsr8_6/design.v \
    $RTL_LIB/lfsr9_7/design.v \
    $RTL_LIB/lfsr10_8/design.v \
    $RTL_LIB/lfsr11_9/design.v \
    $RTL_LIB/lfsr12_10/design.v \
    $RTL_LIB/lfsr13_11/design.v \
    $RTL_LIB/lfsr14_12/design.v \
    $RTL_LIB/lfsr15_13/design.v \
    $RTL_LIB/lfsr16_14/design.v \
    $RTL_LIB/acc2to8/design.v \
    $RTL_LIB/acc2to10/design.v \
    $RTL_LIB/acc2to12/design.v \
    $RTL_LIB/acc2to14/design.v \
    $RTL_LIB/acc2to16/design.v \
    $RTL_LIB/acc3to8/design.v \
    $RTL_LIB/acc3to10/design.v \
    $RTL_LIB/acc3to12/design.v \
    $RTL_LIB/acc3to14/design.v \
    $RTL_LIB/acc3to16/design.v \
    $RTL_LIB/acc4to8/design.v \
    $RTL_LIB/acc4to10/design.v \
    $RTL_LIB/acc4to12/design.v \
    $RTL_LIB/acc4to14/design.v \
    $RTL_LIB/acc4to16/design.v \
    $RTL_LIB/acc5to8/design.v \
    $RTL_LIB/acc5to10/design.v \
    $RTL_LIB/acc5to12/design.v \
    $RTL_LIB/acc5to14/design.v \
    $RTL_LIB/acc5to16/design.v \
    $RTL_LIB/acc6to8/design.v \
    $RTL_LIB/acc6to10/design.v \
    $RTL_LIB/acc6to12/design.v \
    $RTL_LIB/acc6to14/design.v \
    $RTL_LIB/acc6to16/design.v \
    $RTL_LIB/acc7to8/design.v \
    $RTL_LIB/acc7to10/design.v \
    $RTL_LIB/acc7to12/design.v \
    $RTL_LIB/acc7to14/design.v \
    $RTL_LIB/acc7to16/design.v
# Bring in the Zynq PS / AXI / la_axi block design + top wrapper:
if {[file exists $BD_TCL]} { source $BD_TCL }

# Top is your board wrapper that instantiates dut_top + la_axi + PS.
synth_design -top design_1_wrapper -part $PART
opt_design
place_design
route_design
write_bitstream -force $OUT/system_b14.bit
write_hw_platform -fixed -force $OUT/system_b14.xsa
puts "BATCH 14 DONE -> $OUT/system_b14.bit"
