module correctness_s2__med19__g14 (
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);
  reg [7:0] w0;
  reg [7:0] w1;
  reg [7:0] w2;
  reg [7:0] w3;
  reg [7:0] w4;
  reg [7:0] w5;
  reg [7:0] w6;
  reg [7:0] w7;
  reg [7:0] w8;
  reg [7:0] w9;
  reg [7:0] w10;
  reg [7:0] w11;
  reg [7:0] w12;
  reg [7:0] w13;
  reg [7:0] w14;
  reg [7:0] w15;
  reg [7:0] w16;
  reg [7:0] w17;
  reg [7:0] w18;
  reg [7:0] a [0:18];
  reg [7:0] b;
  integer i, j, t;
  always @(posedge clk) begin
    if (!rst_n) begin
      y<=0; w0<=0; w1<=0; w2<=0; w3<=0; w4<=0; w5<=0; w6<=0; w7<=0; w8<=0; w9<=0; w10<=0; w11<=0; w12<=0; w13<=0; w14<=0; w15<=0; w16<=0; w17<=0; w18<=0;
    end else begin
      a[0] = x; a[1] = w0; a[2] = w1; a[3] = w2; a[4] = w3; a[5] = w4; a[6] = w5; a[7] = w6; a[8] = w7; a[9] = w8; a[10] = w9; a[11] = w10; a[12] = w11; a[13] = w12; a[14] = w13; a[15] = w14; a[16] = w15; a[17] = w16; a[18] = w17;
      for (i = 0; i < 19; i = i + 1)
        for (j = i + 1; j < 19; j = j + 1)
          if (a[i] > a[j]) begin t = a[i]; a[i] = a[j]; a[j] = t; end
      y <= {8'b0, a[9]};
      w18<=w17; w17<=w16; w16<=w15; w15<=w14; w14<=w13; w13<=w12; w12<=w11; w11<=w10; w10<=w9; w9<=w8; w8<=w7; w7<=w6; w6<=w5; w5<=w4; w4<=w3; w3<=w2; w2<=w1; w1<=w0; w0 <= x;
    end
  end
endmodule
