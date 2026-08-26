module mlp_s2__med19__g9 (
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
      w0 <= 8'd0;
      w1 <= 8'd0;
      w2 <= 8'd0;
      w3 <= 8'd0;
      w4 <= 8'd0;
      w5 <= 8'd0;
      w6 <= 8'd0;
      w7 <= 8'd0;
      w8 <= 8'd0;
      w9 <= 8'd0;
      w10 <= 8'd0;
      w11 <= 8'd0;
      w12 <= 8'd0;
      w13 <= 8'd0;
      w14 <= 8'd0;
      w15 <= 8'd0;
      w16 <= 8'd0;
      w17 <= 8'd0;
      w18 <= 8'd0;
    end else begin
      s[0] = w0;
      s[1] = w1;
      s[2] = w2;
      s[3] = w3;
      s[4] = w4;
      s[5] = w5;
      s[6] = w6;
      s[7] = w7;
      s[8] = w8;
      s[9] = w9;
      s[10] = w10;
      s[11] = w11;
      s[12] = w12;
      s[13] = w13;
      s[14] = w14;
      s[15] = w15;
      s[16] = w16;
      s[17] = w17;
      s[18] = w18;
      for (i = 0; i < 19; i = i + 1)
        for (j = i + 1; j < 19; j = j + 1)
          if (s[i] > s[j]) begin
            t = s[i];
            s[i] = s[j];
            s[j] = t;
          end
      y <= {8'b0, s[9]};
      w18 <= w17;
      w17 <= w16;
      w16 <= w15;
      w15 <= w14;
      w14 <= w13;
      w13 <= w12;
      w12 <= w11;
      w11 <= w10;
      w10 <= w9;
      w9 <= w8;
      w8 <= w7;
      w7 <= w6;
      w6 <= w5;
      w5 <= w4;
      w4 <= w3;
      w3 <= w2;
      w2 <= w1;
      w1 <= w0;
      w0 <= x;
    end
  end
endmodule
