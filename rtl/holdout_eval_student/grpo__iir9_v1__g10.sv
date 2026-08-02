module grpo__iir9_v1__g10 (
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
  reg [15:0] y2w;
  wire [15:0] z = (2*x + r1 + ((9*y)>>4) + ((5*y2w)>>4)) & 16'hffff;
  always @(posedge clk) begin
    if (!rst_n) begin
      y <= 16'd0;
      y2w <= 16'd0;
      r1 <= 16'd0;
      r2 <= 16'd0;
      r3 <= 16'd0;
      r4 <= 16'd0;
      r5 <= 16'd0;
      r6 <= 16'd0;
      r7 <= 16'd0;
      r8 <= 16'd0;
      r9 <= 16'd0;
    end else begin
      y <= z;
      y2w <= y;
      r1 <= (29*x + r2) & 16'hffff;
      r2 <= (34*x + r3) & 16'hffff;
      r3 <= (29*x + r4) & 16'hffff;
      r4 <= (13*x + r5) & 16'hffff;
      r5 <= (18*x + r6) & 16'hffff;
      r6 <= (60*x + r7) & 16'hffff;
      r7 <= (33*x + r8) & 16'hffff;
      r8 <= (62*x + r9) & 16'hffff;
      r9 <= (10*x) & 16'hffff;
    end
  end
endmodule