module sft__iir20__g4 (
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
  reg [15:0] y2;
  always @(posedge clk) begin
    if (!rst_n) begin y<=0; y2<=0; xd1<=0; xd2<=0; xd3<=0; xd4<=0; xd5<=0; xd6<=0; xd7<=0; xd8<=0; xd9<=0; xd10<=0; xd11<=0; xd12<=0; xd13<=0; xd14<=0; xd15<=0; xd16<=0; xd17<=0; xd18<=0; xd19<=0; xd20<=0; end
    else begin
      y <= (8'd3*x + (8'd5*xd1) + (8'd7*xd2) + (8'd9*xd3) + (8'd11*xd4) + (8'd13*xd5) + (8'd15*xd6) + (8'd17*xd7) + (8'd19*xd8) + (8'd21*xd9) + (8'd23*xd10) + (8'd25*xd11) + (8'd27*xd12) + (8'd29*xd13) + (8'd31*xd14) + (8'd33*xd15) + (8'd35*xd16) + (8'd37*xd17) + (8'd39*xd18) + (8'd41*xd19) + (8'd43*xd20) + ((9*y)>>4) + ((5*y2)>>4)) & 16'hFFFF;
      y2 <= y;
      xd20<=xd19; xd19<=xd18; xd18<=xd17; xd17<=xd16; xd16<=xd15; xd15<=xd14; xd14<=xd13; xd13<=xd12; xd12<=xd11; xd11<=xd10; xd10<=xd9; xd9<=xd8; xd8<=xd7; xd7<=xd6; xd6<=xd5; xd5<=xd4; xd4<=xd3; xd3<=xd2; xd2<=xd1; xd1<=x;
    end
  end
endmodule