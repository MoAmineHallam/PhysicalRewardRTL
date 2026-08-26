module mlp_s1__med19__g2 (
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
      for (i = 18; i > 0; i = i - 1)
        for (j = 0; j < i; j = j + 1)
          if (s[j] > s[j+1]) begin
            t = s[j];
            s[j] = s[j+1];
            s[j+1] = t;
          end
      y <= {8'b0, s[9]};
    end
  end
endmodule
