module apiplain__iir5__g0 (
  input clk,
  input rst_n,
  input [7:0] x,
  output reg [15:0] y
);
  reg [7:0] delay_line [0:5];  // x[n], x[n-1], ..., x[n-5]
  reg [15:0] y_prev1, y_prev2; // y[n-1], y[n-2]
  
  integer k;
  wire [15:0] y_full;  // Full precision before truncation
  
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      for (k = 0; k < 6; k = k + 1)
        delay_line[k] <= 8'd0;
      y_prev1 <= 16'd0;
      y_prev2 <= 16'd0;
      y <= 16'd0;
    end else begin
      // Shift delay line: x[n] becomes new x[n-5]
      delay_line[0] <= x;
      for (k = 1; k < 6; k = k + 1)
        delay_line[k] <= delay_line[k-1];
      
      // Update output registers
      y_prev2 <= y_prev1;
      y_prev1 <= y_full[15:0]; // truncated version becomes previous
      y <= y_full[15:0];
    end
  end
  
  // Compute y[n] combinational
  assign y_full = (3 * delay_line[0]) + 
                  (5 * delay_line[1]) + 
                  (7 * delay_line[2]) + 
                  (9 * delay_line[3]) + 
                  (11 * delay_line[4]) + 
                  (13 * delay_line[5]) +
                  ((9 * y_prev1) >> 4) +
                  ((5 * y_prev2) >> 4);
  
endmodule