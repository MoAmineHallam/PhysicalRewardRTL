module sft__iir8_v7__g2 (
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
  reg [15:0] y2;
  wire [31:0] acc = 57*x + 40*xd1 + 15*xd2 + 4*xd3 + 33*xd4 + 61*xd5 + 39*xd6 + 57*xd7 + 30*xd8 + ((9*y)>>4) + ((5*y2)>>4);
  always @(posedge clk) begin
    if (!rst_n) begin y<=0; y2<=0; xd1<=0; xd2<=0; xd3<=0; xd4<=0; xd5<=0; xd6<=0; xd7<=0; xd8<=0; end
    else begin
      y <= acc[15:0];
      y2 <= y;
      xd8<=xd7; xd7<=xd6; xd6<=xd5; xd5<=xd4; xd4<=xd3; xd3<=xd2; xd2<=xd1; xd1<=x;
    end
  end
endmodule
