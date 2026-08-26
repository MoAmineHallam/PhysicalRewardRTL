module sft__med19__g6 (
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
  reg [7:0] l[0:18];
  reg [7:0] s[0:18];
  integer i, j, t;
  always @(posedge clk) begin
    if (!rst_n) begin
      for (i = 0; i < 19; i = i + 1) l[i] <= 8'd0;
      y <= 16'd0;
    end else begin
      l[0] <= x;
      for (i = 1; i < 19; i = i + 1) l[i] <= l[i-1];
      for (i = 0; i < 19; i = i + 1) s[i] <= l[i];
      for (i = 0; i < 18; i = i + 1)
        for (j = i + 1; j < 19; j = j + 1)
          if (s[i] > s[j]) begin t = s[i]; s[i] = s[j]; s[j] = t; end
      y <= {8'b0, s[9]};
    end
  end
  always @(posedge clk) begin
    if (!rst_n) begin w0 <= 8'd0; w1 <= 8'd0; w2 <= 8'd0; w3 <= 8'd0; w4 <= 8'd0; w5 <= 8'd0; w6 <= 8'd0; w7 <= 8'd0; w8 <= 8'd0; w9 <= 8'd0; w10 <= 8'd0; w11 <= 8'd0; w12 <= 8'd0; w13 <= 8'd0; w14 <= 8'd0; w15 <= 8'd0; w16 <= 8'd0; w17 <= 8'd0; w18 <= 8'd0; end
    else begin
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
    end
  end
endmodule
