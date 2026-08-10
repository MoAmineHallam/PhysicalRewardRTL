module sft__med11__g7 (
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
  reg [7:0] l [0:10];
  reg [7:0] s [0:10];
  integer i, j, t;
  always @(posedge clk) begin
    if (!rst_n) begin
      y<=0; w0<=0; w1<=0; w2<=0; w3<=0; w4<=0; w5<=0; w6<=0; w7<=0; w8<=0; w9<=0;
    end else begin
      l[0] = x; l[1] = w0; l[2] = w1; l[3] = w2; l[4] = w3; l[5] = w4; l[6] = w5; l[7] = w6; l[8] = w7; l[9] = w8; l[10] = w9;
      for (i = 0; i < 11; i = i + 1) for (j = i + 1; j < 11; j = j + 1) if (l[i] > l[j]) begin t = l[i]; l[i] = l[j]; l[j] = t; end
      s[0]=l[0]; s[1]=l[1]; s[2]=l[2]; s[3]=l[3]; s[4]=l[4]; s[5]=l[5]; s[6]=l[6]; s[7]=l[7]; s[8]=l[8]; s[9]=l[9]; s[10]=l[10];
      y <= s[5];
      w0<=x; w1<=w0; w2<=w1; w3<=w2; w4<=w3; w5<=w4; w6<=w5; w7<=w6; w8<=w7; w9<=w8;
    end
  end
endmodule