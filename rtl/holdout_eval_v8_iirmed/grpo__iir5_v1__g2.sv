module grpo__iir5_v1__g2 (
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);
  reg [15:0] r1;
  reg [15:0] r2;
  reg [15:0] r3;
  reg [15:0] r4;
  reg [15:0] r5;
  reg [15:0] y2;
  wire [31:0] acc = 23*x + r1 + ((9*y)>>4) + ((5*y2)>>4);
  always @(posedge clk) begin
    if (!rst_n) begin
      r1 <= 16'd0;
      r2 <= 16'd0;
      r3 <= 16'd0;
      r4 <= 16'd0;
      r5 <= 16'd0;
      y <= 16'd0;
      y2 <= 16'd0;
    end else begin
      r1 <= (5*x + r2) & 16'hffff;
      r2 <= (53*x + r3) & 16'hffff;
      r3 <= (56*x + r4) & 16'hffff;
      r4 <= (8*x + r5) & 16'hffff;
      r5 <= (27*x) & 16'hffff;
      y <= acc & 16'hffff;
      y2 <= y;
    end
  end
endmodule