create_clock -name vclk -period 10.0 [get_ports {clk}]
set nonclock_inputs [get_ports -quiet -filter {DIRECTION == IN && NAME != clk}]
if {[llength $nonclock_inputs]} { set_input_delay -clock [get_clocks vclk] 0.000 $nonclock_inputs }
set all_outputs [get_ports -quiet -filter {DIRECTION == OUT}]
if {[llength $all_outputs]} { set_output_delay -clock [get_clocks vclk] 0.000 $all_outputs }
