module mlp_s2__med21__g0 (
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
  reg [7:0] w19;
  reg [7:0] w20;
  reg [7:0] l [0:20];
  reg [7:0] s [0:20];
  integer i, j, t;
  always @(posedge clk) begin
    if (!rst_n) begin
      l[0] <= 8'd0;
      l[1] <= 8'd0;
      l[2] <= 8'd0;
      l[3] <= 8'd0;
      l[4] <= 8'd0;
      l[5] <= 8'd0;
      l[6] <= 8'd0;
      l[7] <= 8'd0;
      l[8] <= 8'd0;
      l[9] <= 8'd0;
      l[10] <= 8'd0;
      l[11] <= 8'd0;
      l[12] <= 8'd0;
      l[13] <= 8'd0;
      l[14] <= 8'd0;
      l[15] <= 8'd0;
      l[16] <= 8'd0;
      l[17] <= 8'd0;
      l[18] <= 8'd0;
      l[19] <= 8'd0;
      l[20] <= 8'd0;
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
      w19 <= 8'd0;
      w20 <= 8'd0;
      y <= 16'd0;
    end else begin
      l[0] <= x;
      for (i = 1; i < 21; i = i + 1) begin
        l[i] <= l[i-1];
      end
      for (i = 0; i < 21; i = i + 1) begin
        s[i] <= l[i];
      end
      for (i = 0; i < 20; i = i + 1) begin
        for (j = i + 1; j < 21; j = j + 1) begin
          if (s[i] > s[j]) begin
            t = s[i];
            s[i] = s[j];
            s[j] = t;
          end
        end
      end
      y <= {8'd0, s[10]};
      w0 <= x;
      w1 <= w0;
      w2 <= w1;
      w3 <= w2;
      w4 <= w3;
      w5 <= w4;
      w6 <= w5;
      w7 <= w6;
      w8 <= w7;
      w9 <= w8;
      w10 <= w9;
      w11 <= w10;
      w12 <= w11;
      w13 <= w12;
      w14 <= w13;
      w15 <= w14;
      w16 <= w15;
      w17 <= w16;
      w18 <= w17;
      w19 <= w18;
      w20 <= w19;
    end
  end
endmodule
