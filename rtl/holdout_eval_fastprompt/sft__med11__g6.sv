module sft__med11__g6 (
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);
  reg [7:0] s [0:10];
  reg [7:0] t;
  integer i, j, k;
  reg [15:0] a [0:10];
  always @(*) begin
    for (i = 0; i < 11; i = i + 1) a[i] = {8'd0, s[i]};
    for (i = 0; i < 10; i = i + 1)
      for (j = i + 1; j < 11; j = j + 1)
        if (a[i] > a[j]) begin t = a[i]; a[i] = a[j]; a[j] = t; end
    y <= a[5];
  end
  always @(posedge clk) begin
    if (!rst_n) begin
      for (k = 0; k < 11; k = k + 1) s[k] <= 8'd0;
      y <= 16'd0;
    end else begin
      s[0] <= x;
      for (i = 1; i < 11; i = i + 1) s[i] <= s[i-1];
    end
  end
endmodule