module grpo__med11__g13 (
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
  reg [7:0] m [0:10];
  reg [7:0] t;
  integer i, j;
  always @(posedge clk) begin
    if (!rst_n) begin
      y<=0; w0<=0; w1<=0; w2<=0; w3<=0; w4<=0; w5<=0; w6<=0; w7<=0; w8<=0; w9<=0;
    end else begin
      m[0] = x; m[1] = w0; m[2] = w1; m[3] = w2; m[4] = w3; m[5] = w4; m[6] = w5; m[7] = w6; m[8] = w7; m[9] = w8; m[10] = w9;
      for (i = 0; i < 10; i = i + 1)
        for (j = i + 1; j < 11; j = j + 1)
          if (m[i] > m[j]) begin t = m[i]; m[i] = m[j]; m[j] = t; end
      y <= {8'b0, m[5]};
      w9<=w8; w8<=w7; w7<=w6; w6<=w5; w5<=w4; w4<=w3; w3<=w2; w2<=w1; w1<=w0; w0<=x;
    end
  end
endmodule