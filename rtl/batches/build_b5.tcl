# Auto-generated headless Vivado build  -  batch 5.
# ---- fill these in once for your board/project ----
set PART   "xc7z020clg400-1"        ;# PYNQ-Z2 part
set BD_TCL "$::env(HOME)/pynq_bd.tcl";# your block design (Zynq PS + AXI + la_axi) hook
# ---------------------------------------------------
set ROOT   "/home/user/FPGA"
set RTL_LIB "/home/user/FPGA/rtl_library"
set OUT    "$ROOT/rtl/batches/out_b5"
file mkdir $OUT

create_project -in_memory -part $PART
read_verilog $ROOT/rtl/la_axi.v
read_verilog $ROOT/rtl/batches/dut_top_b5.v
read_verilog $RTL_LIB/step2_cnt13b/design.v \
    $RTL_LIB/step3_cnt13b/design.v \
    $RTL_LIB/step4_cnt13b/design.v \
    $RTL_LIB/step5_cnt13b/design.v \
    $RTL_LIB/step6_cnt13b/design.v \
    $RTL_LIB/step7_cnt13b/design.v \
    $RTL_LIB/step8_cnt13b/design.v \
    $RTL_LIB/step9_cnt13b/design.v \
    $RTL_LIB/step10_cnt13b/design.v \
    $RTL_LIB/step11_cnt13b/design.v \
    $RTL_LIB/step12_cnt13b/design.v \
    $RTL_LIB/step13_cnt13b/design.v \
    $RTL_LIB/step15_cnt13b/design.v \
    $RTL_LIB/step2_cnt14b/design.v \
    $RTL_LIB/step3_cnt14b/design.v \
    $RTL_LIB/step4_cnt14b/design.v \
    $RTL_LIB/step5_cnt14b/design.v \
    $RTL_LIB/step6_cnt14b/design.v \
    $RTL_LIB/step7_cnt14b/design.v \
    $RTL_LIB/step8_cnt14b/design.v \
    $RTL_LIB/step9_cnt14b/design.v \
    $RTL_LIB/step10_cnt14b/design.v \
    $RTL_LIB/step11_cnt14b/design.v \
    $RTL_LIB/step12_cnt14b/design.v \
    $RTL_LIB/step13_cnt14b/design.v \
    $RTL_LIB/step15_cnt14b/design.v \
    $RTL_LIB/downcnt2b/design.v \
    $RTL_LIB/downcnt3b/design.v \
    $RTL_LIB/downcnt4b/design.v \
    $RTL_LIB/downcnt5b/design.v \
    $RTL_LIB/downcnt6b/design.v \
    $RTL_LIB/downcnt7b/design.v \
    $RTL_LIB/downcnt8b/design.v \
    $RTL_LIB/downcnt9b/design.v \
    $RTL_LIB/downcnt10b/design.v \
    $RTL_LIB/downcnt11b/design.v \
    $RTL_LIB/downcnt12b/design.v \
    $RTL_LIB/downcnt13b/design.v \
    $RTL_LIB/downcnt14b/design.v \
    $RTL_LIB/downcnt15b/design.v \
    $RTL_LIB/downcnt16b/design.v \
    $RTL_LIB/graycnt3b/design.v \
    $RTL_LIB/graycnt4b/design.v \
    $RTL_LIB/graycnt5b/design.v \
    $RTL_LIB/graycnt6b/design.v \
    $RTL_LIB/graycnt7b/design.v \
    $RTL_LIB/graycnt8b/design.v \
    $RTL_LIB/graycnt9b/design.v \
    $RTL_LIB/graycnt10b/design.v \
    $RTL_LIB/graycnt11b/design.v \
    $RTL_LIB/graycnt12b/design.v \
    $RTL_LIB/graycnt13b/design.v \
    $RTL_LIB/graycnt14b/design.v \
    $RTL_LIB/graycnt15b/design.v \
    $RTL_LIB/graycnt16b/design.v \
    $RTL_LIB/ring3/design.v \
    $RTL_LIB/johnson3/design.v \
    $RTL_LIB/ring4/design.v \
    $RTL_LIB/johnson4/design.v \
    $RTL_LIB/ring5/design.v \
    $RTL_LIB/johnson5/design.v \
    $RTL_LIB/ring6/design.v \
    $RTL_LIB/johnson6/design.v \
    $RTL_LIB/ring7/design.v
# Bring in the Zynq PS / AXI / la_axi block design + top wrapper:
if {[file exists $BD_TCL]} { source $BD_TCL }

# Top is your board wrapper that instantiates dut_top + la_axi + PS.
synth_design -top design_1_wrapper -part $PART
opt_design
place_design
route_design
write_bitstream -force $OUT/system_b5.bit
write_hw_platform -fixed -force $OUT/system_b5.xsa
puts "BATCH 5 DONE -> $OUT/system_b5.bit"
