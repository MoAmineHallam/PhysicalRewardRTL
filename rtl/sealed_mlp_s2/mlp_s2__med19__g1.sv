module mlp_s2__med19__g1 (
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
  reg [7:0] l [0:18];
  reg [7:0] r [0:18];
  integer i, j, m;
  always @(posedge clk) begin
    if (!rst_n) begin
      for (i = 0; i < 19; i = i + 1) l[i] <= 8'd0;
      for (i = 0; i < 19; i = i + 1) r[i] <= 8'd0;
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
      y <= 16'd0;
    end else begin
      l[0] <= x;
      r[0] <= w0;
      for (i = 1; i < 19; i = i + 1) begin
        l[i] <= l[i-1];
        r[i] <= r[i-1];
      end
      for (i = 0; i < 18; i = i + 1) for (j = i+1; j < 19; j = j + 1) if (l[i] > l[j]) begin m = l[i]; l[i] = l[j]; l[j] = m; end
      for (i = 0; i < 18; i = i + 1) for (j = i+1; j < 19; j = j + 1) if (r[i] > r[j]) begin m = r[i]; r[i] = r[j]; r[j] = m; end
      y <= {8'd0, l[9]};
      w0 <= w1;
      w1 <= w2;
      w2 <= w3;
      w3 <= w4;
      w4 <= w5;
      w5 <= w6;
      w6 <= w7;
      w7 <= w8;
      w8 <= w9;
      w9 <= w10;
      w10 <= w11;
      w11 <= w12;
      w12 <= w13;
      w13 <= w14;
      w14 <= w15;
      w15 <= w16;
      w16 <= w17;
      w17 <= w18;
      w18 <= x;
    end
  end
endmodule
