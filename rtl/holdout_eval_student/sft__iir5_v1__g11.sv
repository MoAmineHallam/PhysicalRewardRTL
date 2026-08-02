module sft__iir5_v1__g11 (
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);
  reg [15:0] r0;
  reg [15:0] r1;
  reg [15:0] r2;
  reg [15:0] r3;
  reg [15:0] r4;
  reg [15:0] y2;
  wire [31:0] acc = 23*x + r0 + ((9*y)>>4) + ((5*y2)>>4);
  always @(posedge clk) begin
    if (!rst_n) begin
      y <= 0;
      y2 <= 0;
      r0 <= 0;
      r1 <= 0;
      r2 <= 0;
      r3 <= 0;
      r4 <= 0;
    end else begin
      y <= acc[15:0];
      y2 <= y;
      r0 <= (5*x + r1) & 16'hFFFF;
      r1 <= (53*x + r2) & 16'hFFFF;
      r2 <= (56*x + r3) & 16'hFFFF;
      r3 <= (8*x + r4) & 16'hFFFF;
      r4 <= (27*x) & 16'hFFFF;
    end
  end
endmodule