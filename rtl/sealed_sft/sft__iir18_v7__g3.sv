module sft__iir18_v7__g3 (
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);
  reg [15:0] a1;
  reg [15:0] a2;
  reg [15:0] a3;
  reg [15:0] a4;
  reg [15:0] a5;
  reg [15:0] a6;
  reg [15:0] a7;
  reg [15:0] a8;
  reg [15:0] a9;
  reg [15:0] a10;
  reg [15:0] a11;
  reg [15:0] a12;
  reg [15:0] a13;
  reg [15:0] a14;
  reg [15:0] a15;
  reg [15:0] a16;
  reg [15:0] a17;
  reg [15:0] a18;
  reg [15:0] y2;
  wire [31:0] acc = 25*x + a1 + ((9*y)>>4) + ((5*y2)>>4);
  always @(posedge clk) begin
    if (!rst_n) begin y<=0; y2<=0; a1<=0; a2<=0; a3<=0; a4<=0; a5<=0; a6<=0; a7<=0; a8<=0; a9<=0; a10<=0; a11<=0; a12<=0; a13<=0; a14<=0; a15<=0; a16<=0; a17<=0; a18<=0; end
    else begin
      y <= acc[15:0];
      y2 <= y;
      a1 <= (26*x + a2) & 16'hFFFF;
      a2 <= (46*x + a3) & 16'hFFFF;
      a3 <= (49*x + a4) & 16'hFFFF;
      a4 <= (16*x + a5) & 16'hFFFF;
      a5 <= (8*x + a6) & 16'hFFFF;
      a6 <= (15*x + a7) & 16'hFFFF;
      a7 <= (31*x + a8) & 16'hFFFF;
      a8 <= (37*x + a9) & 16'hFFFF;
      a9 <= (52*x + a10) & 16'hFFFF;
      a10 <= (6*x + a11) & 16'hFFFF;
      a11 <= (54*x + a12) & 16'hFFFF;
      a12 <= (60*x + a13) & 16'hFFFF;
      a13 <= (33*x + a14) & 16'hFFFF;
      a14 <= (33*x + a15) & 16'hFFFF;
      a15 <= (62*x + a16) & 16'hFFFF;
      a16 <= (48*x + a17) & 16'hFFFF;
      a17 <= (18*x + a18) & 16'hFFFF;
      a18 <= (56*x) & 16'hFFFF;
    end
  end
endmodule
