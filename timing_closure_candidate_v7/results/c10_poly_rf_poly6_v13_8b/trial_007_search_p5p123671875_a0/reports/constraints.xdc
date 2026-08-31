create_clock -name vclk -period 5.123671875 [get_ports {clk}]
set_input_delay -clock [get_clocks vclk] 0.000 [get_ports -quiet -filter {DIRECTION == IN && NAME != clk}]
set_output_delay -clock [get_clocks vclk] 0.000 [get_ports -quiet -filter {DIRECTION == OUT}]
