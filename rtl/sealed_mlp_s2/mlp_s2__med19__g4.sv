module mlp_s2__med19__g4 (
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
  reg [7:0] w11;
  reg [7:0] w12;
  reg [7:0] w13;
  reg [7:0] w14;
  reg [7:0] w15;
  reg [7:0] w16;
  reg [7:0] w17;
  reg [7:0] w18;
  reg [7:0] s [0:18];
  reg [7:0] t;
  integer i, j;

  always @(posedge clk) begin
    if (!rst_n) begin
      for (i = 0; i < 19; i = i + 1) s[i] <= 8'd0;
      y <= 16'd0;
    end else begin
      s[0] <= x;
      for (i = 1; i < 19; i = i + 1) s[i] <= s[i-1];
      for (i = 0; i < 18; i = i + 1)
        for (j = i + 1; j < 19; j = j + 1)
          if (s[i] > s[j]) begin t = s[i]; s[i] = s[j]; s[j] = t; end
      y <= {8'd0, s[9]};
    end
  end
endmodule
