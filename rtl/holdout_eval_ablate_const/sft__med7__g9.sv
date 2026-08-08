module sft__med7__g9 (
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);
  reg [7:0] w0;
  reg [7:0] w1;
  reg [7:0] w2;
  reg [7:0] w3;
  reg [7:0] w4;
  reg [7:0] w5;
  reg [7:0] arr [0:6];
  reg [7:0] t0;
  reg [7:0] t1;
  reg [7:0] t2;
  reg [7:0] t3;
  reg [7:0] t4;
  reg [7:0] t5;
  integer i, j, k;
  always @(posedge clk) begin
    if (!rst_n) begin
      y<=0; w0<=0; w1<=0; w2<=0; w3<=0; w4<=0; w5<=0;
    end else begin
      arr[0] = x;
      arr[1] = w0;
      arr[2] = w1;
      arr[3] = w2;
      arr[4] = w3;
      arr[5] = w4;
      arr[6] = w5;
      for (i = 0; i < 7; i = i + 1)
        for (j = 0; j < 6 - i; j = j + 1)
          if (arr[j] > arr[j+1]) begin t0 = arr[j]; arr[j] = arr[j+1]; arr[j+1] = t0; end
      y <= {8'b0, arr[3]};
      w5<=w4; w4<=w3; w3<=w2; w2<=w1; w1<=w0; w0<=x;
    end
  end
endmodule