module sft__iir9_v1__g2 (
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
  wire [31:0] acc = 8'd2 * x + r1 + ((9*y)>>4) + ((5*y2)>>4);
  always @(posedge clk) begin
    if (!rst_n) begin
      y <= 0;
      y2 <= 0;
      r1 <= 0;
      r2 <= 0;
      r3 <= 0;
      r4 <= 0;
      r5 <= 0;
      r6 <= 0;
      r7 <= 0;
      r8 <= 0;
      r9 <= 0;
    end else begin
      y <= acc[15:0];
      y2 <= y;
      r1 <= (8'd29 * x + r2) & 16'hFFFF;
      r2 <= (8'd34 * x + r3) & 16'hFFFF;
      r3 <= (8'd29 * x + r4) & 16'hFFFF;
      r4 <= (8'd13 * x + r5) & 16'hFFFF;
      r5 <= (8'd18 * x + r6) & 16'hFFFF;
      r6 <= (8'd60 * x + r7) & 16'hFFFF;
      r7 <= (8'd33 * x + r8) & 16'hFFFF;
      r8 <= (8'd62 * x + r9) & 16'hFFFF;
      r9 <= (8'd10 * x) & 16'hFFFF;
    end
  end
endmodule