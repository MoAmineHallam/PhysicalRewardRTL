module sft__iir5__g3 (
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);
  reg [7:0] xd1;
  reg [7:0] xd2;
  reg [7:0] xd3;
  reg [7:0] xd4;
  reg [7:0] xd5;
  reg [15:0] y2;
  reg [15:0] y3;
  reg [15:0] y4;
  reg [15:0] y5;
  wire [31:0] acc = 3*x + 5*xd1 + 7*xd2 + 9*xd3 + 11*xd4 + 13*xd5 + ((9*y)>>4) + ((5*y2)>>4);
  always @(posedge clk) begin
    if (!rst_n) begin y<=0; y2<=0; y3<=0; y4<=0; y5<=0; xd1<=0; xd2<=0; xd3<=0; xd4<=0; xd5<=0; end
    else begin
      y <= acc[15:0];
      y2 <= y;
      y3 <= y2;
      y4 <= y3;
      y5 <= y4;
      xd5<=xd4; xd4<=xd3; xd3<=xd2; xd2<=xd1; xd1 <= x;
    end
  end
endmodule