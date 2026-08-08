module grpo__med11__g6 (
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
  reg [7:0] tmp [0:10];
  integer i, j, k;
  always @(posedge clk) begin
    if (!rst_n) begin
      y<=0; w0<=0; w1<=0; w2<=0; w3<=0; w4<=0; w5<=0; w6<=0; w7<=0; w8<=0; w9<=0;
    end else begin
      tmp[0] = x;
      tmp[1] = w0;
      tmp[2] = w1;
      tmp[3] = w2;
      tmp[4] = w3;
      tmp[5] = w4;
      tmp[6] = w5;
      tmp[7] = w6;
      tmp[8] = w7;
      tmp[9] = w8;
      tmp[10] = w9;
      for (i = 0; i < 11; i = i + 1)
        for (j = 0; j < 11 - i - 1; j = j + 1)
          if (tmp[j] > tmp[j+1]) begin k = tmp[j]; tmp[j] = tmp[j+1]; tmp[j+1] = k; end
      y <= {8'b0, tmp[5]};
      w9<=w8; w8<=w7; w7<=w6; w6<=w5; w5<=w4; w4<=w3; w3<=w2; w2<=w1; w1<=w0; w0<=x;
    end
  end
endmodule