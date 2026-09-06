module rf_s4__med21__g1 (
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
  reg [7:0] s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12, s13, s14, s15, s16, s17, s18, s19, s20;
  reg [7:0] arr [0:20];
  integer i, j, k;
  always @(posedge clk) begin
    if (!rst_n) begin
      y<=0; w0<=0; w1<=0; w2<=0; w3<=0; w4<=0; w5<=0; w6<=0; w7<=0; w8<=0; w9<=0; w10<=0; w11<=0; w12<=0; w13<=0; w14<=0; w15<=0; w16<=0; w17<=0; w18<=0; w19<=0; w20<=0;
    end else begin
      arr[0] = x;
      arr[1] = w0;
      arr[2] = w1;
      arr[3] = w2;
      arr[4] = w3;
      arr[5] = w4;
      arr[6] = w5;
      arr[7] = w6;
      arr[8] = w7;
      arr[9] = w8;
      arr[10] = w9;
      arr[11] = w10;
      arr[12] = w11;
      arr[13] = w12;
      arr[14] = w13;
      arr[15] = w14;
      arr[16] = w15;
      arr[17] = w16;
      arr[18] = w17;
      arr[19] = w18;
      arr[20] = w19;
      for (i = 0; i < 21; i = i + 1)
        for (j = 0; j < 20; j = j + 1)
          if (arr[j] > arr[j+1]) begin s0 = arr[j]; arr[j] = arr[j+1]; arr[j+1] = s0; end
      y <= {8'b0, arr[10]};
      w0 <= x;
      w1 <= w0;
      w2 <= w1;
      w3 <= w2;
      w4 <= w3;
      w5 <= w4;
      w6 <= w5;
      w7 <= w6;
      w8 <= w7;
      w9 <= w8;
      w10 <= w9;
      w11 <= w10;
      w12 <= w11;
      w13 <= w12;
      w14 <= w13;
      w15 <= w14;
      w16 <= w15;
      w17 <= w16;
      w18 <= w17;
      w19 <= w18;
      w20 <= w19;
    end
  end
endmodule
