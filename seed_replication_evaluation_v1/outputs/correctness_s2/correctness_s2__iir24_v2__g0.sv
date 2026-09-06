module correctness_s2__iir24_v2__g0 (
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
  reg [7:0] xd19;
  reg [7:0] xd20;
  reg [7:0] xd21;
  reg [7:0] xd22;
  reg [7:0] xd23;
  reg [7:0] xd24;
  reg [15:0] y2;
  wire [31:0] acc = 63*x + 15*xd1 + 4*xd2 + 35*xd3 + 41*xd4 + 47*xd5 + 40*xd6 + 2*xd7 + 60*xd8 + 19*xd9 + 5*xd10 + 12*xd11 + 50*xd12 + 28*xd13 + 46*xd14 + 49*xd15 + 15*xd16 + 22*xd17 + 36*xd18 + 52*xd19 + 8*xd20 + 31*xd21 + 50*xd22 + 57*xd23 + 45*xd24 + ((9*y)>>4) + ((5*y2)>>4);
  always @(posedge clk) begin
    if (!rst_n) begin y<=0; y2<=0; xd1<=0; xd2<=0; xd3<=0; xd4<=0; xd5<=0; xd6<=0; xd7<=0; xd8<=0; xd9<=0; xd10<=0; xd11<=0; xd12<=0; xd13<=0; xd14<=0; xd15<=0; xd16<=0; xd17<=0; xd18<=0; xd19<=0; xd20<=0; xd21<=0; xd22<=0; xd23<=0; xd24<=0; end
    else begin
      y <= acc[15:0];
      y2 <= y;
      xd24<=xd23; xd23<=xd22; xd22<=xd21; xd21<=xd20; xd20<=xd19; xd19<=xd18; xd18<=xd17; xd17<=xd16; xd16<=xd15; xd15<=xd14; xd14<=xd13; xd13<=xd12; xd12<=xd11; xd11<=xd10; xd10<=xd9; xd9<=xd8; xd8<=xd7; xd7<=xd6; xd6<=xd5; xd5<=xd4; xd4<=xd3; xd3<=xd2; xd2<=xd1; xd1<=x;
    end
  end
endmodule
