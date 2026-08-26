module sft__med21__g13 (
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);
  reg [7:0] window [0:20];
  integer i, j, k;
  reg [7:0] t;
  reg [7:0] s [0:20];
  always @(posedge clk) begin
    if (!rst_n) begin
      for (i = 0; i < 21; i = i + 1) window[i] <= 8'd0;
      y <= 16'd0;
    end else begin
      window[0] <= x;
      for (i = 1; i < 21; i = i + 1) window[i] <= window[i-1];
      for (i = 0; i < 21; i = i + 1) s[i] <= window[i];
      for (i = 0; i < 20; i = i + 1)
        for (j = 0; j < 20 - i; j = j + 1)
          if (s[j] > s[j+1]) begin t = s[j]; s[j] = s[j+1]; s[j+1] = t; end
      y <= {8'b0, s[10]};
    end
  end
endmodule
