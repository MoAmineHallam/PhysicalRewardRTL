module sft__med21__g6 (
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
  reg [7:0] ws [0:20];
  reg [7:0] sorted [0:20];
  integer i, j, t;
  always @(posedge clk) begin
    if (!rst_n) begin
      y<=0; w0<=0; w1<=0; w2<=0; w3<=0; w4<=0; w5<=0; w6<=0; w7<=0; w8<=0; w9<=0; w10<=0; w11<=0; w12<=0; w13<=0; w14<=0; w15<=0; w16<=0; w17<=0; w18<=0; w19<=0; ws[0]<=0; ws[1]<=0; ws[2]<=0; ws[3]<=0; ws[4]<=0; ws[5]<=0; ws[6]<=0; ws[7]<=0; ws[8]<=0; ws[9]<=0; ws[10]<=0; ws[11]<=0; ws[12]<=0; ws[13]<=0; ws[14]<=0; ws[15]<=0; ws[16]<=0; ws[17]<=0; ws[18]<=0; ws[19]<=0; ws[20]<=0;
    end else begin
      ws[0] <= x;
      ws[1]<=w0; ws[2]<=w1; ws[3]<=w2; ws[4]<=w3; ws[5]<=w4; ws[6]<=w5; ws[7]<=w6; ws[8]<=w7; ws[9]<=w8; ws[10]<=w9; ws[11]<=w10; ws[12]<=w11; ws[13]<=w12; ws[14]<=w13; ws[15]<=w14; ws[16]<=w15; ws[17]<=w16; ws[18]<=w17; ws[19]<=w18; ws[20]<=w19;
      for (i = 0; i < 21; i = i + 1) sorted[i] = ws[i];
      for (i = 0; i < 20; i = i + 1)
        for (j = i + 1; j < 21; j = j + 1)
          if (sorted[i] > sorted[j]) begin t = sorted[i]; sorted[i] = sorted[j]; sorted[j] = t; end
      y <= {8'b0, sorted[10]};
      w19<=w9; w18<=w8; w17<=w7; w16<=w6; w15<=w5; w14<=w4; w13<=w3; w12<=w2; w11<=w1; w10<=w0;
      w9<=x; w8<=w19; w7<=w18; w6<=w17; w5<=w16; w4<=w15; w3<=w14; w2<=w13; w1<=w12; w0<=w11;
    end
  end
endmodule
