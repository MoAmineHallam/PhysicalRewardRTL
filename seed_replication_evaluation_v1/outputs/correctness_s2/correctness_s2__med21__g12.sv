module correctness_s2__med21__g12 (
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);
  reg [7:0] w [0:20];
  reg [7:0] t;
  integer i, j, k;
  reg [7:0] s [0:20];
  always @(posedge clk) begin
    if (!rst_n) begin
      for (i = 0; i < 21; i = i + 1) w[i] <= 8'd0;
      y <= 16'd0;
    end else begin
      w[0] <= x;
      for (i = 1; i < 21; i = i + 1) w[i] <= w[i-1];
      for (i = 0; i < 21; i = i + 1) s[i] <= w[i];
      for (i = 0; i < 20; i = i + 1)
        for (j = i + 1; j < 21; j = j + 1)
          if (s[i] > s[j]) begin t = s[i]; s[i] = s[j]; s[j] = t; end
      y <= {8'd0, s[10]};
    end
  end
endmodule
