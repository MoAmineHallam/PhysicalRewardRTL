# Auto-generated headless Vivado build  -  batch 6.
# ---- fill these in once for your board/project ----
set PART   "xc7z020clg400-1"        ;# PYNQ-Z2 part
set BD_TCL "$::env(HOME)/pynq_bd.tcl";# your block design (Zynq PS + AXI + la_axi) hook
# ---------------------------------------------------
set ROOT   "/home/user/FPGA"
set RTL_LIB "/home/user/FPGA/rtl_library"
set OUT    "$ROOT/rtl/batches/out_b6"
file mkdir $OUT

create_project -in_memory -part $PART
read_verilog $ROOT/rtl/la_axi.v
read_verilog $ROOT/rtl/batches/dut_top_b6.v
read_verilog $RTL_LIB/johnson7/design.v \
    $RTL_LIB/ring8/design.v \
    $RTL_LIB/johnson8/design.v \
    $RTL_LIB/ring9/design.v \
    $RTL_LIB/johnson9/design.v \
    $RTL_LIB/ring10/design.v \
    $RTL_LIB/johnson10/design.v \
    $RTL_LIB/ring12/design.v \
    $RTL_LIB/johnson12/design.v \
    $RTL_LIB/ring16/design.v \
    $RTL_LIB/johnson16/design.v \
    $RTL_LIB/tccnt4_15/design.v \
    $RTL_LIB/tccnt4_8/design.v \
    $RTL_LIB/tccnt4_5/design.v \
    $RTL_LIB/tccnt4_4/design.v \
    $RTL_LIB/tccnt4_12/design.v \
    $RTL_LIB/tccnt5_31/design.v \
    $RTL_LIB/tccnt5_16/design.v \
    $RTL_LIB/tccnt5_10/design.v \
    $RTL_LIB/tccnt5_8/design.v \
    $RTL_LIB/tccnt5_24/design.v \
    $RTL_LIB/tccnt6_63/design.v \
    $RTL_LIB/tccnt6_32/design.v \
    $RTL_LIB/tccnt6_21/design.v \
    $RTL_LIB/tccnt6_16/design.v \
    $RTL_LIB/tccnt6_48/design.v \
    $RTL_LIB/tccnt7_127/design.v \
    $RTL_LIB/tccnt7_64/design.v \
    $RTL_LIB/tccnt7_42/design.v \
    $RTL_LIB/tccnt7_32/design.v \
    $RTL_LIB/tccnt7_96/design.v \
    $RTL_LIB/tccnt8_255/design.v \
    $RTL_LIB/tccnt8_128/design.v \
    $RTL_LIB/tccnt8_85/design.v \
    $RTL_LIB/tccnt8_64/design.v \
    $RTL_LIB/tccnt8_192/design.v \
    $RTL_LIB/sipo_l3b/design.v \
    $RTL_LIB/sipo_r3b/design.v \
    $RTL_LIB/sipo_l4b/design.v \
    $RTL_LIB/sipo_r4b/design.v \
    $RTL_LIB/sipo_l5b/design.v \
    $RTL_LIB/sipo_r5b/design.v \
    $RTL_LIB/sipo_l6b/design.v \
    $RTL_LIB/sipo_r6b/design.v \
    $RTL_LIB/sipo_l7b/design.v \
    $RTL_LIB/sipo_r7b/design.v \
    $RTL_LIB/sipo_l8b/design.v \
    $RTL_LIB/sipo_r8b/design.v \
    $RTL_LIB/sipo_l9b/design.v \
    $RTL_LIB/sipo_r9b/design.v \
    $RTL_LIB/sipo_l10b/design.v \
    $RTL_LIB/sipo_r10b/design.v \
    $RTL_LIB/sipo_l11b/design.v \
    $RTL_LIB/sipo_r11b/design.v \
    $RTL_LIB/sipo_l12b/design.v \
    $RTL_LIB/sipo_r12b/design.v \
    $RTL_LIB/sipo_l13b/design.v \
    $RTL_LIB/sipo_r13b/design.v \
    $RTL_LIB/sipo_l14b/design.v \
    $RTL_LIB/sipo_r14b/design.v \
    $RTL_LIB/sipo_l15b/design.v \
    $RTL_LIB/sipo_r15b/design.v \
    $RTL_LIB/sipo_l16b/design.v \
    $RTL_LIB/sipo_r16b/design.v
# Bring in the Zynq PS / AXI / la_axi block design + top wrapper:
if {[file exists $BD_TCL]} { source $BD_TCL }

# Top is your board wrapper that instantiates dut_top + la_axi + PS.
synth_design -top design_1_wrapper -part $PART
opt_design
place_design
route_design
write_bitstream -force $OUT/system_b6.bit
write_hw_platform -fixed -force $OUT/system_b6.xsa
puts "BATCH 6 DONE -> $OUT/system_b6.bit"
