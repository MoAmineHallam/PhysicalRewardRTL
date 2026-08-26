module rf_mid_s2__med19__g3 (
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);
  reg [7:0] l0, l1, l2, l3, l4, l5, l6, l7, l8, l9, l10, l11, l12, l13, l14, l15, l16, l17, l18;
  reg [7:0] t0, t1, t2, t3, t4, t5, t6, t7, t8, t9, t10, t11, t12, t13, t14, t15, t16, t17, t18;
  reg [7:0] u0, u1, u2, u3, u4, u5, u6, u7, u8, u9, u10, u11, u12, u13, u14, u15, u16, u17, u18;
  wire [7:0] s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12, s13, s14, s15, s16, s17, s18;
  reg [7:0] sw[0:18];
  reg [7:0] w0, w1, w2, w3, w4, w5, w6, w7, w8, w9, w10, w11, w12, w13, w14, w15, w16, w17, w18;
  integer i, j, k;
  always @(posedge clk) begin
    if (!rst_n) begin
      l0 <= 8'd0; l1 <= 8'd0; l2 <= 8'd0; l3 <= 8'd0; l4 <= 8'd0; l5 <= 8'd0; l6 <= 8'd0; l7 <= 8'd0; l8 <= 8'd0; l9 <= 8'd0; l10 <= 8'd0; l11 <= 8'd0; l12 <= 8'd0; l13 <= 8'd0; l14 <= 8'd0; l15 <= 8'd0; l16 <= 8'd0; l17 <= 8'd0; l18 <= 8'd0;
      y <= 16'd0;
    end else begin
      l0 <= x; l1 <= l0; l2 <= l1; l3 <= l2; l4 <= l3; l5 <= l4; l6 <= l5; l7 <= l6; l8 <= l7; l9 <= l8; l10 <= l9; l11 <= l10; l12 <= l11; l13 <= l12; l14 <= l13; l15 <= l14; l16 <= l15; l17 <= l16; l18 <= l17;
      t0 <= l0; t1 <= l1; t2 <= l2; t3 <= l3; t4 <= l4; t5 <= l5; t6 <= l6; t7 <= l7; t8 <= l8; t9 <= l9; t10 <= l10; t11 <= l11; t12 <= l12; t13 <= l13; t14 <= l14; t15 <= l15; t16 <= l16; t17 <= l17; t18 <= l18;
      u0 <= t0; u1 <= t1; u2 <= t2; u3 <= t3; u4 <= t4; u5 <= t5; u6 <= t6; u7 <= t7; u8 <= t8; u9 <= t9; u10 <= t10; u11 <= t11; u12 <= t12; u13 <= t13; u14 <= t14; u15 <= t15; u16 <= t16; u17 <= t17; u18 <= t18;
      sw[0] = u0; sw[1] = u1; sw[2] = u2; sw[3] = u3; sw[4] = u4; sw[5] = u5; sw[6] = u6; sw[7] = u7; sw[8] = u8; sw[9] = u9; sw[10] = u10; sw[11] = u11; sw[12] = u12; sw[13] = u13; sw[14] = u14; sw[15] = u15; sw[16] = u16; sw[17] = u17; sw[18] = u18;
      w0 = sw[0]; w1 = sw[1]; w2 = sw[2]; w3 = sw[3]; w4 = sw[4]; w5 = sw[5]; w6 = sw[6]; w7 = sw[7]; w8 = sw[8]; w9 = sw[9]; w10 = sw[10]; w11 = sw[11]; w12 = sw[12]; w13 = sw[13]; w14 = sw[14]; w15 = sw[15]; w16 = sw[16]; w17 = sw[17]; w18 = sw[18];
      for (i = 0; i < 18; i = i + 1) begin
        for (j = 0; j < 18 - i; j = j + 1) begin
          if (sw[j] > sw[j + 1]) begin k = sw[j]; sw[j] = sw[j + 1]; sw[j + 1] = k; end
        end
      end
      y <= {8'b0, sw[9]};
    end
  end
endmodule
