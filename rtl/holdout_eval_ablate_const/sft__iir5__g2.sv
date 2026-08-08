module sft__iir5__g2 (
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);
  reg [15:0] r1;
  reg [15:0] r2;
  reg [15:0] r3;
  reg [15:0] r4;
  reg [15:0] r5;
  reg [15:0] y2;
  reg [7:0] xd1;
  reg [7:0] xd2;
  reg [7:0] xd3;
  reg [7:0] xd4;
  reg [7:0] xd5;
  wire [31:0] acc = 3*x + 5*xd1 + 7*xd2 + 9*xd3 + 11*xd4 + 13*xd5 + ((9*y)>>4) + ((5*y2)>>4);
  always @(posedge clk) begin
    if (!rst_n) begin y<=0; y2<=0; r1<=0; r2<=0; r3<=0; r4<=0; r5<=0; xd1<=0; xd2<=0; xd3<=0; xd4<=0; xd5<=0; end
    else begin
      y <= acc[15:0];
      y2 <= y;
      r1 <= (8*x + ((9*y)>>4)) & 16'hFFFF;
      r2 <= (8*xd1 + 10*x + ((9*y)>>4) + ((1*y2)>>4)) & 16'hFFFF;
      r3 <= (8*xd2 + 10*xd1 + 12*x + ((9*y)>>4) + ((1*y2)>>4)) & 16'hFFFF;
      r4 <= (8*xd3 + 10*xd2 + 12*xd1 + 14*x + ((9*y)>>4) + ((1*y2)>>4)) & 16'hFFFF;
      r5 <= (8*xd4 + 10*xd3 + 12*xd2 + 14*xd1 + 16*x + ((9*y)>>4) + ((1*y2)>>4)) & 16'hFFFF;
      xd5<=xd4; xd4<=xd3; xd3<=xd2; xd2<=xd1; xd1<=x;
    end
  end
endmodule