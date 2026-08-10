module grpo__med7__g2 (
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);
  reg [7:0] w0;
  reg [7:0] w1;
  reg [7:0] w2;
  reg [7:0] w3;
  reg [7:0] w4;
  reg [7:0] w5;
  reg [7:0] s [0:6];
  reg [7:0] t;
  integer i, j;
  always @(posedge clk) begin
    if (!rst_n) begin
      y<=0; w0<=0; w1<=0; w2<=0; w3<=0; w4<=0; w5<=0;
    end else begin
      s[0] = x; s[1] = w0; s[2] = w1; s[3] = w2; s[4] = w3; s[5] = w4; s[6] = w5;
      for (i = 0; i < 7; i = i + 1)
        for (j = i + 1; j < 7; j = j + 1)
          if (s[i] > s[j]) begin t = s[i]; s[i] = s[j]; s[j] = t; end
      y <= {8'b0, s[3]};
      w5<=w4; w4<=w3; w3<=w2; w2<=w1; w1<=w0; w0<=x;
    end
  end
endmodule