module apifast__iir5__g0 (
  input clk,
  input rst_n,
  input [7:0] x,
  output reg [15:0] y
);

  // Pipeline registers for input samples
  reg [7:0] x0, x1, x2, x3, x4, x5;
  
  // Pipeline registers for output samples
  reg [15:0] y1, y2;
  
  // Stage 1: Multiply inputs by coefficients and register results
  reg [15:0] m0, m1, m2, m3, m4, m5;
  wire [15:0] m0_next, m1_next, m2_next, m3_next, m4_next, m5_next;
  
  assign m0_next = x0 * 8'd3;
  assign m1_next = x1 * 8'd5;
  assign m2_next = x2 * 8'd7;
  assign m3_next = x3 * 8'd9;
  assign m4_next = x4 * 8'd11;
  assign m5_next = x5 * 8'd13;
  
  // Stage 2: Sum feedforward terms
  reg [19:0] ff_sum; // 20 bits to accommodate sum of 6 products
  wire [19:0] ff_sum_next;
  assign ff_sum_next = m0 + m1 + m2 + m3 + m4 + m5;
  
  // Feedback terms with shift: (9*y1)>>4 and (5*y2)>>4
  reg [15:0] fb1, fb2;
  wire [15:0] fb1_next, fb2_next;
  assign fb1_next = {4'b0, y1[15:4]} + {4'b0, y1[15:4]} + {4'b0, y1[15:4]} + 
                    {4'b0, y1[15:4]} + {4'b0, y1[15:4]} + {4'b0, y1[15:4]} + 
                    {4'b0, y1[15:4]} + {4'b0, y1[15:4]} + {4'b0, y1[15:4]};
  // This is 9 * (y1>>4). Using shift and add: 9*y1>>4 = (y1>>4) + (y1>>4<<3) = (y1>>4) + (y1>>1)
  // But simpler: compute as ((9*y1)>>4) directly
  // Re-implement clearly:
  // fb1_next = (9 * y1) >> 4;
  // Since 9 = 8+1: ( (y1<<3) + y1 ) >> 4 = (y1 + (y1<<3)) >> 4
  // We'll compute in 20-bit domain for safety
  
  wire [19:0] y1_20 = {4'b0, y1};
  wire [19:0] y2_20 = {4'b0, y2};
  wire [19:0] fb1_20 = ( (y1_20 << 3) + y1_20 ) >> 4; // 9*y1>>4
  wire [19:0] fb2_20 = ( (y2_20 << 2) + y2_20 ) >> 4; // 5*y2>>4 = (4*y2 + y2)>>4
  
  assign fb1_next = fb1_20[15:0];
  assign fb2_next = fb2_20[15:0];
  
  // Stage 3: Sum everything + register
  reg [19:0] total;
  wire [19:0] total_next;
  assign total_next = ff_sum + fb1_20 + fb2_20;
  
  // Output register and state update pipeline
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      x0 <= 8'd0;
      x1 <= 8'd0;
      x2 <= 8'd0;
      x3 <= 8'd0;
      x4 <= 8'd0;
      x5 <= 8'd0;
      m0 <= 16'd0;
      m1 <= 16'd0;
      m2 <= 16'd0;
      m3 <= 16'd0;
      m4 <= 16'd0;
      m5 <= 16'd0;
      ff_sum <= 20'd0;
      fb1 <= 16'd0;
      fb2 <= 16'd0;
      total <= 20'd0;
      y <= 16'd0;
      y1 <= 16'd0;
      y2 <= 16'd0;
    end else begin
      // Input pipeline
      x0 <= x;
      x1 <= x0;
      x2 <= x1;
      x3 <= x2;
      x4 <= x3;
      x5 <= x4;
      
      // Stage 1 outputs
      m0 <= m0_next;
      m1 <= m1_next;
      m2 <= m2_next;
      m3 <= m3_next;
      m4 <= m4_next;
      m5 <= m5_next;
      
      // Stage 2 outputs
      ff_sum <= ff_sum_next;
      fb1 <= fb1_next;
      fb2 <= fb2_next;
      
      // Stage 3 total
      total <= total_next;
      
      // Output registers (with extra pipeline for y1/y2)
      y <= total_next[15:0];
      y1 <= total_next[15:0];
      y2 <= y1;
    end
  end

endmodule