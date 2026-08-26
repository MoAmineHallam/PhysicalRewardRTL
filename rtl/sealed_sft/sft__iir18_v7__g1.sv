module sft__iir18_v7__g1 (
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);
  reg [7:0] xd1;
  reg [7:0] xd2;
  reg [7:0] xd3;
  reg [7:0] xd4;
  reg [7:0] xd5;
  reg [7:0] xd6;
  reg [7:0] xd7;
  reg [7:0] xd8;
  reg [7:0] xd9;
  reg [7:0] xd10;
  reg [7:0] xd11;
  reg [7:0] xd12;
  reg [7:0] xd13;
  reg [7:0] xd14;
  reg [7:0] xd15;
  reg [7:0] xd16;
  reg [7:0] xd17;
  reg [7:0] xd18;
  reg [15:0] y2;
  wire [31:0] acc = 25*x + 26*xd1 + 46*xd2 + 49*xd3 + 16*xd4 + 8*xd5 + 15*xd6 + 31*xd7 + 37*xd8 + 52*xd9 + 6*xd10 + 54*xd11 + 60*xd12 + 33*xd13 + 33*xd14 + 62*xd15 + 48*xd16 + 18*xd17 + 56*xd18 + ((9*y)>>4) + ((5*y2)>>4);
  always @(posedge clk) begin
    if (!rst_n) begin y<=0; y2<=0; xd1<=0; xd2<=0; xd3<=0; xd4<=0; xd5<=0; xd6<=0; xd7<=0; xd8<=0; xd9<=0; xd10<=0; xd11<=0; xd12<=0; xd13<=0; xd14<=0; xd15<=0; xd16<=0; xd17<=0; xd18<=0; end
    else begin
      y <= acc[15:0];
      y2 <= y;
      xd18<=xd17; xd17<=xd16; xd16<=xd15; xd15<=xd14; xd14<=xd13; xd13<=xd12; xd12<=xd11; xd11<=xd10; xd10<=xd9; xd9<=xd8; xd8<=xd7; xd7<=xd6; xd6<=xd5; xd5<=xd4; xd4<=xd3; xd3<=xd2; xd2<=xd1; xd1 <= x;
    end
  end
endmodule
