module sft__med7__g4 (
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);
  reg [7:0] w0;
  reg [7:0] w1;
  reg [7:0] w2;
  reg [7:0] w3;
  reg [7:0] w4;
  reg [7:0] w5;
  reg [7:0] a [0:6];
  reg [7:0] t;
  integer i, j;
  always @(posedge clk) begin
    if (!rst_n) begin
      y<=0; w0<=0; w1<=0; w2<=0; w3<=0; w4<=0; w5<=0;
    end else begin
      a[0] = x; a[1] = w0; a[2] = w1; a[3] = w2; a[4] = w3; a[5] = w4; a[6] = w5;
      for (i = 0; i < 7; i = i + 1)
        for (j = 0; j < 6; j = j + 1)
          if (a[j] > a[j+1]) begin t = a[j]; a[j] = a[j+1]; a[j+1] = t; end
      y <= {8'b0, a[3]};
      w5<=w4; w4<=w3; w3<=w2; w2<=w1; w1<=w0; w0<=x;
    end
  end
endmodule