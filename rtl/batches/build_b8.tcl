# Auto-generated headless Vivado build  -  batch 8.
# ---- fill these in once for your board/project ----
set PART   "xc7z020clg400-1"        ;# PYNQ-Z2 part
set BD_TCL "$::env(HOME)/pynq_bd.tcl";# your block design (Zynq PS + AXI + la_axi) hook
# ---------------------------------------------------
set ROOT   "/home/user/FPGA"
set RTL_LIB "/home/user/FPGA/rtl_library"
set OUT    "$ROOT/rtl/batches/out_b8"
file mkdir $OUT

create_project -in_memory -part $PART
read_verilog $ROOT/rtl/la_axi.v
read_verilog $ROOT/rtl/batches/dut_top_b8.v
read_verilog $RTL_LIB/sub5b/design.v \
    $RTL_LIB/addsub5b/design.v \
    $RTL_LIB/add6b/design.v \
    $RTL_LIB/sub6b/design.v \
    $RTL_LIB/addsub6b/design.v \
    $RTL_LIB/add7b/design.v \
    $RTL_LIB/sub7b/design.v \
    $RTL_LIB/addsub7b/design.v \
    $RTL_LIB/add8b/design.v \
    $RTL_LIB/sub8b/design.v \
    $RTL_LIB/addsub8b/design.v \
    $RTL_LIB/add9b/design.v \
    $RTL_LIB/sub9b/design.v \
    $RTL_LIB/addsub9b/design.v \
    $RTL_LIB/add10b/design.v \
    $RTL_LIB/sub10b/design.v \
    $RTL_LIB/addsub10b/design.v \
    $RTL_LIB/add11b/design.v \
    $RTL_LIB/sub11b/design.v \
    $RTL_LIB/addsub11b/design.v \
    $RTL_LIB/add12b/design.v \
    $RTL_LIB/sub12b/design.v \
    $RTL_LIB/addsub12b/design.v \
    $RTL_LIB/add13b/design.v \
    $RTL_LIB/sub13b/design.v \
    $RTL_LIB/addsub13b/design.v \
    $RTL_LIB/add14b/design.v \
    $RTL_LIB/sub14b/design.v \
    $RTL_LIB/addsub14b/design.v \
    $RTL_LIB/add15b/design.v \
    $RTL_LIB/sub15b/design.v \
    $RTL_LIB/addsub15b/design.v \
    $RTL_LIB/satadd3b/design.v \
    $RTL_LIB/satadd4b/design.v \
    $RTL_LIB/satadd5b/design.v \
    $RTL_LIB/satadd6b/design.v \
    $RTL_LIB/satadd7b/design.v \
    $RTL_LIB/satadd8b/design.v \
    $RTL_LIB/satadd9b/design.v \
    $RTL_LIB/satadd10b/design.v \
    $RTL_LIB/satadd11b/design.v \
    $RTL_LIB/satadd12b/design.v \
    $RTL_LIB/satadd13b/design.v \
    $RTL_LIB/satadd14b/design.v \
    $RTL_LIB/satadd15b/design.v \
    $RTL_LIB/logical_lsh4/design.v \
    $RTL_LIB/rotate_lsh4/design.v \
    $RTL_LIB/logical_rsh4/design.v \
    $RTL_LIB/rotate_rsh4/design.v \
    $RTL_LIB/logical_lsh5/design.v \
    $RTL_LIB/logical_rsh5/design.v \
    $RTL_LIB/logical_lsh6/design.v \
    $RTL_LIB/logical_rsh6/design.v \
    $RTL_LIB/logical_lsh7/design.v \
    $RTL_LIB/logical_rsh7/design.v \
    $RTL_LIB/logical_lsh8/design.v \
    $RTL_LIB/rotate_lsh8/design.v \
    $RTL_LIB/logical_rsh8/design.v \
    $RTL_LIB/rotate_rsh8/design.v \
    $RTL_LIB/logical_lsh10/design.v \
    $RTL_LIB/logical_rsh10/design.v \
    $RTL_LIB/logical_lsh12/design.v \
    $RTL_LIB/logical_rsh12/design.v \
    $RTL_LIB/logical_lsh16/design.v
# Bring in the Zynq PS / AXI / la_axi block design + top wrapper:
if {[file exists $BD_TCL]} { source $BD_TCL }

# Top is your board wrapper that instantiates dut_top + la_axi + PS.
synth_design -top design_1_wrapper -part $PART
opt_design
place_design
route_design
write_bitstream -force $OUT/system_b8.bit
write_hw_platform -fixed -force $OUT/system_b8.xsa
puts "BATCH 8 DONE -> $OUT/system_b8.bit"
