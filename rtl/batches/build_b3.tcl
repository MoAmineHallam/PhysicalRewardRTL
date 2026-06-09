# Auto-generated headless Vivado build  -  batch 3.
# ---- fill these in once for your board/project ----
set PART   "xc7z020clg400-1"        ;# PYNQ-Z2 part
set BD_TCL "$::env(HOME)/pynq_bd.tcl";# your block design (Zynq PS + AXI + la_axi) hook
# ---------------------------------------------------
set ROOT   "/home/user/FPGA"
set RTL_LIB "/home/user/FPGA/rtl_library"
set OUT    "$ROOT/rtl/batches/out_b3"
file mkdir $OUT

create_project -in_memory -part $PART
read_verilog $ROOT/rtl/la_axi.v
read_verilog $ROOT/rtl/batches/dut_top_b3.v
read_verilog $RTL_LIB/updown5b/design.v \
    $RTL_LIB/updown6b/design.v \
    $RTL_LIB/updown7b/design.v \
    $RTL_LIB/updown8b/design.v \
    $RTL_LIB/updown9b/design.v \
    $RTL_LIB/updown10b/design.v \
    $RTL_LIB/updown11b/design.v \
    $RTL_LIB/updown12b/design.v \
    $RTL_LIB/updown13b/design.v \
    $RTL_LIB/updown14b/design.v \
    $RTL_LIB/updown15b/design.v \
    $RTL_LIB/step2_cnt4b/design.v \
    $RTL_LIB/step3_cnt4b/design.v \
    $RTL_LIB/step4_cnt4b/design.v \
    $RTL_LIB/step5_cnt4b/design.v \
    $RTL_LIB/step6_cnt4b/design.v \
    $RTL_LIB/step7_cnt4b/design.v \
    $RTL_LIB/step8_cnt4b/design.v \
    $RTL_LIB/step9_cnt4b/design.v \
    $RTL_LIB/step10_cnt4b/design.v \
    $RTL_LIB/step11_cnt4b/design.v \
    $RTL_LIB/step12_cnt4b/design.v \
    $RTL_LIB/step13_cnt4b/design.v \
    $RTL_LIB/step15_cnt4b/design.v \
    $RTL_LIB/step2_cnt5b/design.v \
    $RTL_LIB/step3_cnt5b/design.v \
    $RTL_LIB/step4_cnt5b/design.v \
    $RTL_LIB/step5_cnt5b/design.v \
    $RTL_LIB/step6_cnt5b/design.v \
    $RTL_LIB/step7_cnt5b/design.v \
    $RTL_LIB/step8_cnt5b/design.v \
    $RTL_LIB/step9_cnt5b/design.v \
    $RTL_LIB/step10_cnt5b/design.v \
    $RTL_LIB/step11_cnt5b/design.v \
    $RTL_LIB/step12_cnt5b/design.v \
    $RTL_LIB/step13_cnt5b/design.v \
    $RTL_LIB/step15_cnt5b/design.v \
    $RTL_LIB/step2_cnt6b/design.v \
    $RTL_LIB/step3_cnt6b/design.v \
    $RTL_LIB/step4_cnt6b/design.v \
    $RTL_LIB/step5_cnt6b/design.v \
    $RTL_LIB/step6_cnt6b/design.v \
    $RTL_LIB/step7_cnt6b/design.v \
    $RTL_LIB/step8_cnt6b/design.v \
    $RTL_LIB/step9_cnt6b/design.v \
    $RTL_LIB/step10_cnt6b/design.v \
    $RTL_LIB/step11_cnt6b/design.v \
    $RTL_LIB/step12_cnt6b/design.v \
    $RTL_LIB/step13_cnt6b/design.v \
    $RTL_LIB/step15_cnt6b/design.v \
    $RTL_LIB/step2_cnt7b/design.v \
    $RTL_LIB/step3_cnt7b/design.v \
    $RTL_LIB/step4_cnt7b/design.v \
    $RTL_LIB/step5_cnt7b/design.v \
    $RTL_LIB/step6_cnt7b/design.v \
    $RTL_LIB/step7_cnt7b/design.v \
    $RTL_LIB/step8_cnt7b/design.v \
    $RTL_LIB/step9_cnt7b/design.v \
    $RTL_LIB/step10_cnt7b/design.v \
    $RTL_LIB/step11_cnt7b/design.v \
    $RTL_LIB/step12_cnt7b/design.v \
    $RTL_LIB/step13_cnt7b/design.v \
    $RTL_LIB/step15_cnt7b/design.v \
    $RTL_LIB/step2_cnt8b/design.v
# Bring in the Zynq PS / AXI / la_axi block design + top wrapper:
if {[file exists $BD_TCL]} { source $BD_TCL }

# Top is your board wrapper that instantiates dut_top + la_axi + PS.
synth_design -top design_1_wrapper -part $PART
opt_design
place_design
route_design
write_bitstream -force $OUT/system_b3.bit
write_hw_platform -fixed -force $OUT/system_b3.xsa
puts "BATCH 3 DONE -> $OUT/system_b3.bit"
