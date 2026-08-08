module sft__iir5_v1__g2 (
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);
  reg [15:0] r1;
  reg [15:0] r2;
  reg [15:0] r3;
  reg [15:0] r4;
  reg [15:0] r5;
  reg [15:0] y2;
  wire [31:0] acc = 23*x + 5*r1 + 53*r2 + 56*r3 + 8*r4 + 27*r5 + ((9*y)>>4) + ((5*y2)>>4);
  always @(posedge clk) begin
    if (!rst_n) begin y<=0; y2<=0; r1<=0; r2<=0; r3<=0; r4<=0; r5<=0; end
    else begin
      y <= acc[15:0];
      y2 <= y;
      r1 <= x;
      r2 <= r1;
      r3 <= r2;
      r4 <= r3;
      r5 <= r4;
    end
  end
endmodule