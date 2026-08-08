module grpo__iir20__g7 (
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
  wire [31:0] acc = 3*x + (5*xd1) + (7*xd2) + (9*xd3) + (11*xd4) + (13*xd5) + (15*xd6) + (17*xd7) + (19*xd8) + (21*xd9) + (23*xd10) + (25*xd11) + (27*xd12) + (29*xd13) + (31*xd14) + (33*xd15) + (35*xd16) + (37*xd17) + (39*xd18) + (41*xd19) + (43*xd20) + ((9*y)>>4) + ((5*y2)>>4);
  always @(posedge clk) begin
    if (!rst_n) begin y<=0; y2<=0; xd1<=0; xd2<=0; xd3<=0; xd4<=0; xd5<=0; xd6<=0; xd7<=0; xd8<=0; xd9<=0; xd10<=0; xd11<=0; xd12<=0; xd13<=0; xd14<=0; xd15<=0; xd16<=0; xd17<=0; xd18<=0; xd19<=0; xd20<=0; end
    else begin
      y <= acc[15:0];
      y2 <= y;
      xd20<=xd19; xd19<=xd18; xd18<=xd17; xd17<=xd16; xd16<=xd15; xd15<=xd14; xd14<=xd13; xd13<=xd12; xd12<=xd11; xd11<=xd10; xd10<=xd9; xd9<=xd8; xd8<=xd7; xd7<=xd6; xd6<=xd5; xd5<=xd4; xd4<=xd3; xd3<=xd2; xd2<=xd1; xd1 <= x;
    end
  end
endmodule