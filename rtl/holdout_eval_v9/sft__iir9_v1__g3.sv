module sft__iir9_v1__g3 (
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
  reg [15:0] y2;
  wire [31:0] acc = 2*x + xd1*29 + xd2*34 + xd3*29 + xd4*13 + xd5*18 + xd6*60 + xd7*33 + xd8*62 + xd9*10 + ((9*y)>>4) + ((5*y2)>>4);
  always @(posedge clk) begin
    if (!rst_n) begin y<=0; y2<=0; xd1<=0; xd2<=0; xd3<=0; xd4<=0; xd5<=0; xd6<=0; xd7<=0; xd8<=0; xd9<=0; end
    else begin
      y <= acc[15:0];
      y2 <= y;
      xd9<=xd8; xd8<=xd7; xd7<=xd6; xd6<=xd5; xd5<=xd4; xd4<=xd3; xd3<=xd2; xd2<=xd1; xd1 <= x;
    end
  end
endmodule