module rf_s3__med19__g1 (
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
  reg [7:0] s [0:18];
  reg [7:0] t;
  integer i, j;
  always @(posedge clk) begin
    if (!rst_n) begin
      y<=0; w0<=0; w1<=0; w2<=0; w3<=0; w4<=0; w5<=0; w6<=0; w7<=0; w8<=0; w9<=0; w10<=0; w11<=0; w12<=0; w13<=0; w14<=0; w15<=0; w16<=0; w17<=0; w18<=0;
    end else begin
      s[0] = x;
      s[1] = w0;
      s[2] = w1;
      s[3] = w2;
      s[4] = w3;
      s[5] = w4;
      s[6] = w5;
      s[7] = w6;
      s[8] = w7;
      s[9] = w8;
      s[10] = w9;
      s[11] = w10;
      s[12] = w11;
      s[13] = w12;
      s[14] = w13;
      s[15] = w14;
      s[16] = w15;
      s[17] = w16;
      s[18] = w17;
      for (i = 0; i < 19; i = i + 1)
        for (j = 0; j < 19 - i; j = j + 1)
          if (s[j] > s[j+1]) begin t = s[j]; s[j] = s[j+1]; s[j+1] = t; end
      y <= {8'b0, s[9]};
      w18<=w17; w17<=w16; w16<=w15; w15<=w14; w14<=w13; w13<=w12; w12<=w11; w11<=w10; w10<=w9; w9<=w8; w8<=w7; w7<=w6; w6<=w5; w5<=w4; w4<=w3; w3<=w2; w2<=w1; w1<=w0; w0 <= x;
    end
  end
endmodule
