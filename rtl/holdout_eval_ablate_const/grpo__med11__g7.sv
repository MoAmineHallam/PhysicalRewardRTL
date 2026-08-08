module grpo__med11__g7 (
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
  reg [31:0] sorter [0:10];
  reg [7:0] tmp0;
  reg [7:0] tmp1;
  reg [7:0] tmp2;
  reg [7:0] tmp3;
  reg [7:0] tmp4;
  reg [7:0] tmp5;
  reg [7:0] tmp6;
  reg [7:0] tmp7;
  reg [7:0] tmp8;
  reg [7:0] tmp9;
  reg [7:0] tmp10;
  integer i, j, argmin;
  always @(posedge clk) begin
    if (!rst_n) begin
      y<=0; w0<=0; w1<=0; w2<=0; w3<=0; w4<=0; w5<=0; w6<=0; w7<=0; w8<=0; w9<=0; w10<=0;
    end else begin
      sorter[0] = x;
      sorter[1] = w0;
      sorter[2] = w1;
      sorter[3] = w2;
      sorter[4] = w3;
      sorter[5] = w4;
      sorter[6] = w5;
      sorter[7] = w6;
      sorter[8] = w7;
      sorter[9] = w8;
      sorter[10] = w9;
      for (i = 0; i < 11; i = i + 1)
        for (j = i+1; j < 11; j = j + 1)
          if (sorter[i] > sorter[j]) begin
            tmp0 = sorter[i]; sorter[i] = sorter[j]; sorter[j] = tmp0;
          end
      y <= {8'b0, sorter[5]};
      w10<=w9; w9<=w8; w8<=w7; w7<=w6; w6<=w5; w5<=w4; w4<=w3; w3<=w2; w2<=w1; w1<=w0; w0<=x;
    end
  end
endmodule