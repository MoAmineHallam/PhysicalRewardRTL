module sft__iir5_v1__g8 (
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);
  reg [15:0] r1;
  reg [15:0] r2;
  reg [15:0] r3;
  reg [15:0] r4;
  reg [15:0] r5;
  reg [15:0] y2;
  reg [15:0] y3;
  wire [31:0] acc = 23*x + r1 + ((9*y)>>4) + ((5*y2)>>4);
  always @(posedge clk) begin
    if (!rst_n) begin
      y <= 0;
      y2 <= 0;
      y3 <= 0;
      r1 <= 0;
      r2 <= 0;
      r3 <= 0;
      r4 <= 0;
      r5 <= 0;
    end else begin
      y <= acc[15:0];
      y2 <= y;
      y3 <= y2;
      r1 <= 5*x + r2;
      r2 <= 53*x + r3;
      r3 <= 56*x + r4;
      r4 <= 8*x + r5;
      r5 <= 27*x;
    end
  end
endmodule