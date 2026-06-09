# Auto-generated headless Vivado build  -  batch 4.
# ---- fill these in once for your board/project ----
set PART   "xc7z020clg400-1"        ;# PYNQ-Z2 part
set BD_TCL "$::env(HOME)/pynq_bd.tcl";# your block design (Zynq PS + AXI + la_axi) hook
# ---------------------------------------------------
set ROOT   "/home/user/FPGA"
set RTL_LIB "/home/user/FPGA/rtl_library"
set OUT    "$ROOT/rtl/batches/out_b4"
file mkdir $OUT

create_project -in_memory -part $PART
read_verilog $ROOT/rtl/la_axi.v
read_verilog $ROOT/rtl/batches/dut_top_b4.v
read_verilog $RTL_LIB/step3_cnt8b/design.v \
    $RTL_LIB/step4_cnt8b/design.v \
    $RTL_LIB/step5_cnt8b/design.v \
    $RTL_LIB/step6_cnt8b/design.v \
    $RTL_LIB/step7_cnt8b/design.v \
    $RTL_LIB/step8_cnt8b/design.v \
    $RTL_LIB/step9_cnt8b/design.v \
    $RTL_LIB/step10_cnt8b/design.v \
    $RTL_LIB/step11_cnt8b/design.v \
    $RTL_LIB/step12_cnt8b/design.v \
    $RTL_LIB/step13_cnt8b/design.v \
    $RTL_LIB/step15_cnt8b/design.v \
    $RTL_LIB/step2_cnt9b/design.v \
    $RTL_LIB/step3_cnt9b/design.v \
    $RTL_LIB/step4_cnt9b/design.v \
    $RTL_LIB/step5_cnt9b/design.v \
    $RTL_LIB/step6_cnt9b/design.v \
    $RTL_LIB/step7_cnt9b/design.v \
    $RTL_LIB/step8_cnt9b/design.v \
    $RTL_LIB/step9_cnt9b/design.v \
    $RTL_LIB/step10_cnt9b/design.v \
    $RTL_LIB/step11_cnt9b/design.v \
    $RTL_LIB/step12_cnt9b/design.v \
    $RTL_LIB/step13_cnt9b/design.v \
    $RTL_LIB/step15_cnt9b/design.v \
    $RTL_LIB/step2_cnt10b/design.v \
    $RTL_LIB/step3_cnt10b/design.v \
    $RTL_LIB/step4_cnt10b/design.v \
    $RTL_LIB/step5_cnt10b/design.v \
    $RTL_LIB/step6_cnt10b/design.v \
    $RTL_LIB/step7_cnt10b/design.v \
    $RTL_LIB/step8_cnt10b/design.v \
    $RTL_LIB/step9_cnt10b/design.v \
    $RTL_LIB/step10_cnt10b/design.v \
    $RTL_LIB/step11_cnt10b/design.v \
    $RTL_LIB/step12_cnt10b/design.v \
    $RTL_LIB/step13_cnt10b/design.v \
    $RTL_LIB/step15_cnt10b/design.v \
    $RTL_LIB/step2_cnt11b/design.v \
    $RTL_LIB/step3_cnt11b/design.v \
    $RTL_LIB/step4_cnt11b/design.v \
    $RTL_LIB/step5_cnt11b/design.v \
    $RTL_LIB/step6_cnt11b/design.v \
    $RTL_LIB/step7_cnt11b/design.v \
    $RTL_LIB/step8_cnt11b/design.v \
    $RTL_LIB/step9_cnt11b/design.v \
    $RTL_LIB/step10_cnt11b/design.v \
    $RTL_LIB/step11_cnt11b/design.v \
    $RTL_LIB/step12_cnt11b/design.v \
    $RTL_LIB/step13_cnt11b/design.v \
    $RTL_LIB/step15_cnt11b/design.v \
    $RTL_LIB/step2_cnt12b/design.v \
    $RTL_LIB/step3_cnt12b/design.v \
    $RTL_LIB/step4_cnt12b/design.v \
    $RTL_LIB/step5_cnt12b/design.v \
    $RTL_LIB/step6_cnt12b/design.v \
    $RTL_LIB/step7_cnt12b/design.v \
    $RTL_LIB/step8_cnt12b/design.v \
    $RTL_LIB/step9_cnt12b/design.v \
    $RTL_LIB/step10_cnt12b/design.v \
    $RTL_LIB/step11_cnt12b/design.v \
    $RTL_LIB/step12_cnt12b/design.v \
    $RTL_LIB/step13_cnt12b/design.v \
    $RTL_LIB/step15_cnt12b/design.v
# Bring in the Zynq PS / AXI / la_axi block design + top wrapper:
if {[file exists $BD_TCL]} { source $BD_TCL }

# Top is your board wrapper that instantiates dut_top + la_axi + PS.
synth_design -top design_1_wrapper -part $PART
opt_design
place_design
route_design
write_bitstream -force $OUT/system_b4.bit
write_hw_platform -fixed -force $OUT/system_b4.xsa
puts "BATCH 4 DONE -> $OUT/system_b4.bit"
