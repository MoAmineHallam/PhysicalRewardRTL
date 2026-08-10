module grpo__med11__g2 (
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
  reg [7:0] s [0:10];
  reg [7:0] t;
  integer i, j;
  always @(posedge clk) begin
    if (!rst_n) begin
      y<=0; w0<=0; w1<=0; w2<=0; w3<=0; w4<=0; w5<=0; w6<=0; w7<=0; w8<=0; w9<=0; w10<=0;
    end else begin
      s[0] = x; s[1] = w0; s[2] = w1; s[3] = w2; s[4] = w3; s[5] = w4; s[6] = w5; s[7] = w6; s[8] = w7; s[9] = w8; s[10] = w9;
      for (i = 0; i < 10; i = i + 1)
        for (j = 0; j < 10 - i; j = j + 1)
          if (s[j] > s[j+1]) begin t = s[j]; s[j] = s[j+1]; s[j+1] = t; end
      y <= {8'b0, s[5]};
      w10<=w9; w9<=w8; w8<=w7; w7<=w6; w6<=w5; w5<=w4; w4<=w3; w3<=w2; w2<=w1; w1<=w0; w0 <= x;
    end
  end
endmodule