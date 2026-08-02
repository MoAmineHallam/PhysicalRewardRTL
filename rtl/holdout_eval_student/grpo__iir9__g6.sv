module grpo__iir9__g6 (
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);
  reg [15:0] r1;
  reg [15:0] r2;
  reg [15:0] r3;
  reg [15:0] r4;
  reg [15:0] r5;
  reg [15:0] r6;
  reg [15:0] r7;
  reg [15:0] r8;
  reg [15:0] r9;
  reg [15:0] y2;
  reg [15:0] y3;
  reg [15:0] y4;
  reg [15:0] y5;
  reg [15:0] y6;
  reg [15:0] y7;
  reg [15:0] y8;
  reg [15:0] y9;
  reg [15:0] [7:0] xd1;
  wire [31:0] sum = 3*x + r1 + ((9*y)>>4) + ((5*y2)>>4);
  always @(posedge clk) begin
    if (!rst_n) begin
      y <= 0;
      y2 <= 0;
      y3 <= 0;
      y4 <= 0;
      y5 <= 0;
      y6 <= 0;
      y7 <= 0;
      y8 <= 0;
      y9 <= 0;
      r1 <= 0;
      r2 <= 0;
      r3 <= 0;
      r4 <= 0;
      r5 <= 0;
      r6 <= 0;
      r7 <= 0;
      r8 <= 0;
      r9 <= 0;
      xd1 <= 0;
    end else begin
      y <= sum[15:0];
      y2 <= y;
      y3 <= y2;
      y4 <= y3;
      y5 <= y4;
      y6 <= y5;
      y7 <= y6;
      y8 <= y7;
      y9 <= y8;
      r1 <= (5*x + r2) & 16'hFFFF;
      r2 <= (7*x + r3) & 16'hFFFF;
      r3 <= (9*x + r4) & 16'hFFFF;
      r4 <= (11*x + r5) & 16'hFFFF;
      r5 <= (13*x + r6) & 16'hFFFF;
      r6 <= (15*x + r7) & 16'hFFFF;
      r7 <= (17*x + r8) & 16'hFFFF;
      r8 <= (19*x + r9) & 16'hFFFF;
      r9 <= (21*x) & 16'hFFFF;
      xd1 <= x;
    end
  end
endmodule