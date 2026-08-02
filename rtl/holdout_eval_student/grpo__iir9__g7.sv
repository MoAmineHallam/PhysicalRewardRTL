module grpo__iir9__g7 (
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
  wire [31:0] acc_mod = (3*x + r1) + ((9*y)>>4) + ((5*y2)>>4);
  always @(posedge clk) begin
    if (!rst_n) begin
      r1 <= 16'd0;
      r2 <= 16'd0;
      r3 <= 16'd0;
      r4 <= 16'd0;
      r5 <= 16'd0;
      r6 <= 16'd0;
      r7 <= 16'd0;
      r8 <= 16'd0;
      r9 <= 16'd0;
      y2 <= 16'd0;
      y3 <= 16'd0;
      y4 <= 16'd0;
      y5 <= 16'd0;
      y6 <= 16'd0;
      y7 <= 16'd0;
      y8 <= 16'd0;
      y9 <= 16'd0;
      y <= 16'd0;
    end else begin
      r1 <= (5*x + r2) & 16'hffff;
      r2 <= (7*x + r3) & 16'hffff;
      r3 <= (9*x + r4) & 16'hffff;
      r4 <= (11*x + r5) & 16'hffff;
      r5 <= (13*x + r6) & 16'hffff;
      r6 <= (15*x + r7) & 16'hffff;
      r7 <= (17*x + r8) & 16'hffff;
      r8 <= (19*x + r9) & 16'hffff;
      r9 <= (21*x) & 16'hffff;
      y2 <= y;
      y3 <= y2;
      y4 <= y3;
      y5 <= y4;
      y6 <= y5;
      y7 <= y6;
      y8 <= y7;
      y9 <= y8;
      y <= acc_mod[15:0];
    end
  end
endmodule