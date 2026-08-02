module grpo__iir9_v1__g7 (
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
  reg [15:0] y3;
  reg [15:0] y4;
  reg [15:0] y5;
  reg [15:0] y6;
  reg [15:0] y7;
  reg [15:0] y8;
  reg [15:0] y9;
  reg [15:0] y10;
  wire [31:0] acc = 2*x + (29*xd1) + (34*xd2) + (29*xd3) + (13*xd4) + (18*xd5) + (60*xd6) + (33*xd7) + (62*xd8) + (10*xd9) + ((9*y)>>4) + ((5*y2)>>4);
  always @(posedge clk) begin
    if (!rst_n) begin
      y <= 0;
      y2 <= 0;
      y3 <= 0;
      y4 <= 0;
      y5 <= 0;
      y6 <= 0;
      y7 <= 0;
      y8 <= 0;
      y9 <= 0;
      y10 <= 0;
      xd1 <= 0;
      xd2 <= 0;
      xd3 <= 0;
      xd4 <= 0;
      xd5 <= 0;
      xd6 <= 0;
      xd7 <= 0;
      xd8 <= 0;
      xd9 <= 0;
    end else begin
      y <= acc[15:0];
      y2 <= y;
      y3 <= y2;
      y4 <= y3;
      y5 <= y4;
      y6 <= y5;
      y7 <= y6;
      y8 <= y7;
      y9 <= y8;
      y10 <= y9;
      xd1 <= x;
      xd2 <= xd1;
      xd3 <= xd2;
      xd4 <= xd3;
      xd5 <= xd4;
      xd6 <= xd5;
      xd7 <= xd6;
      xd8 <= xd7;
      xd9 <= xd8;
    end
  end
endmodule