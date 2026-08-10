module sft__iir9__g5 (
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);
  reg [7:0] xd2;
  reg [7:0] xd1;
  reg [7:0] xd0;
  reg [15:0] y2;
  reg [7:0] xd3;
  reg [7:0] xd4;
  reg [7:0] xd5;
  reg [7:0] xd6;
  reg [7:0] xd7;
  reg [7:0] xd8;
  reg [7:0] xd9;
  wire [31:0] acc = 3*xd0 + ((9*y)>>4) + ((5*y2)>>4) + 5*xd1 + 7*xd2 + 9*xd3 + 11*xd4 + 13*xd5 + 15*xd6 + 17*xd7 + 19*xd8 + 21*xd9;
  always @(posedge clk) begin
    if (!rst_n) begin y<=0; y2<=0; xd0<=0; xd1<=0; xd2<=0; xd3<=0; xd4<=0; xd5<=0; xd6<=0; xd7<=0; xd8<=0; xd9<=0; end
    else begin
      y2 <= y;
      y <= acc[15:0];
      xd9<=xd8; xd8<=xd7; xd7<=xd6; xd6<=xd5; xd5<=xd4; xd4<=xd3; xd3<=xd2; xd2<=xd1; xd1<=xd0; xd0 <= x;
    end
  end
endmodule