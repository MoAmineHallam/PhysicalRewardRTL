module apiplain__iir9__g0 (
  input clk,
  input rst_n,
  input [7:0] x,
  output reg [15:0] y
);

  // Feedforward coefficients
  parameter B0 = 3, B1 = 5, B2 = 7, B3 = 9, B4 = 11;
  parameter B5 = 13, B6 = 15, B7 = 17, B8 = 19, B9 = 21;
  
  // Delay line for input samples
  reg [7:0] delay_line [0:9];
  
  // Previous outputs
  reg [15:0] y_del1, y_del2;
  
  // Temporary variables for computation
  reg [15:0] ff_sum;
  reg [15:0] fb_sum;
  reg [15:0] result;
  integer k;
  
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      // Clear all state
      for (k = 0; k < 10; k = k + 1) begin
        delay_line[k] <= 8'd0;
      end
      y_del1 <= 16'd0;
      y_del2 <= 16'd0;
      y <= 16'd0;
    end else begin
      // Update delay line
      delay_line[0] <= x;
      for (k = 1; k < 10; k = k + 1) begin
        delay_line[k] <= delay_line[k-1];
      end
      
      // Compute feedforward sum
      ff_sum = (B0 * delay_line[0]) + 
               (B1 * delay_line[1]) + 
               (B2 * delay_line[2]) + 
               (B3 * delay_line[3]) + 
               (B4 * delay_line[4]) + 
               (B5 * delay_line[5]) + 
               (B6 * delay_line[6]) + 
               (B7 * delay_line[7]) + 
               (B8 * delay_line[8]) + 
               (B9 * delay_line[9]);
      
      // Compute feedback sum: (9*y[n-1])>>4 + (5*y[n-2])>>4
      fb_sum = ((9 * y_del1) >> 4) + ((5 * y_del2) >> 4);
      
      // Compute result and keep only low 16 bits
      result = (ff_sum + fb_sum) & 16'hFFFF;
      
      // Update output registers
      y_del2 <= y_del1;
      y_del1 <= result;
      y <= result;
    end
  end

endmodule