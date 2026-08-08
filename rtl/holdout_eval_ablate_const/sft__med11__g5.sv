module sft__med11__g5 (
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
  reg [7:0] a[0:10];
  reg [7:0] t;
  integer i, j;
  always @(posedge clk) begin
    if (!rst_n) begin
      for (i = 0; i < 11; i = i + 1) a[i] <= 8'd0;
      y <= 16'd0;
    end else begin
      a[0] <= x;
      for (i = 1; i < 11; i = i + 1) a[i] <= a[i - 1];
      for (i = 0; i < 10; i = i + 1)
        for (j = i + 1; j < 11; j = j + 1)
          if (a[i] > a[j]) begin t = a[i]; a[i] = a[j]; a[j] = t; end
      y <= {8'b0, a[5]};
    end
  end
endmodule