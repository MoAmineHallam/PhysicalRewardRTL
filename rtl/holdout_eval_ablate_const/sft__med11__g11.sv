module sft__med11__g11 (
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);
  reg [7:0] s [0:10];
  reg [7:0] t;
  integer i, j, k;
  always @(posedge clk) begin
    if (!rst_n) begin
      for (i = 0; i < 11; i = i + 1) s[i] <= 8'd0;
      y <= 16'd0;
    end else begin
      s[0] <= x;
      for (i = 1; i < 11; i = i + 1) s[i] <= s[i-1];
      for (i = 0; i < 10; i = i + 1)
        for (j = i+1; j < 11; j = j + 1)
          if (s[i] > s[j]) begin t = s[i]; s[i] = s[j]; s[j] = t; end
      y <= {8'b0, s[5]};
    end
  end
endmodule