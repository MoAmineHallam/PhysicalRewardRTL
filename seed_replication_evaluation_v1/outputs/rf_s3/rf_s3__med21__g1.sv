module rf_s3__med21__g1 (
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
  reg [7:0] w19;
  reg [7:0] w20;
  reg [7:0] sorted [0:20];
  reg [7:0] tmp;
  integer i, j;
  always @(posedge clk) begin
    if (!rst_n) begin
      y<=0; w0<=0; w1<=0; w2<=0; w3<=0; w4<=0; w5<=0; w6<=0; w7<=0; w8<=0; w9<=0; w10<=0; w11<=0; w12<=0; w13<=0; w14<=0; w15<=0; w16<=0; w17<=0; w18<=0; w19<=0; w20<=0;
    end else begin
      sorted[0] = x;
      sorted[1] = w0;
      sorted[2] = w1;
      sorted[3] = w2;
      sorted[4] = w3;
      sorted[5] = w4;
      sorted[6] = w5;
      sorted[7] = w6;
      sorted[8] = w7;
      sorted[9] = w8;
      sorted[10] = w9;
      sorted[11] = w10;
      sorted[12] = w11;
      sorted[13] = w12;
      sorted[14] = w13;
      sorted[15] = w14;
      sorted[16] = w15;
      sorted[17] = w16;
      sorted[18] = w17;
      sorted[19] = w18;
      sorted[20] = w19;
      sorted[21] = w20;
      for (i = 0; i < 21; i = i + 1)
        for (j = i + 1; j < 21; j = j + 1)
          if (sorted[i] > sorted[j]) begin
            tmp = sorted[i];
            sorted[i] = sorted[j];
            sorted[j] = tmp;
          end
      y <= {8'b0, sorted[10]};
      w20 <= w19; w19 <= w18; w18 <= w17; w17 <= w16; w16 <= w15; w15 <= w14; w14 <= w13; w13 <= w12; w12 <= w11; w11 <= w10; w10 <= w9; w9 <= w8; w8 <= w7; w7 <= w6; w6 <= w5; w5 <= w4; w4 <= w3; w3 <= w2; w2 <= w1; w1 <= w0; w0<=x;
    end
  end
endmodule
