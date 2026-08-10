module grpo__med7__g4 (
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);
  reg [7:0] w0;
  reg [7:0] w1;
  reg [7:0] w2;
  reg [7:0] w3;
  reg [7:0] w4;
  reg [7:0] w5;
  reg [7:0] s0;
  reg [7:0] s1;
  reg [7:0] s2;
  reg [7:0] s3;
  reg [7:0] s4;
  reg [7:0] s5;
  reg [7:0] t0;
  reg [7:0] t1;
  reg [7:0] t2;
  reg [7:0] t3;
  reg [7:0] t4;
  reg [7:0] t5;
  reg [7:0] t6;
  always @(posedge clk) begin
    if (!rst_n) begin
      y<=0; w0<=0; w1<=0; w2<=0; w3<=0; w4<=0; w5<=0;
    end else begin
      s0 = x; s1 = w0; s2 = w1; s3 = w2; s4 = w3; s5 = w4; t0 = w5;
      if (s0<s1) {s0,s1}={s1,s0}; if (s0<s2) {s0,s2}={s2,s0}; if (s0<s3) {s0,s3}={s3,s0}; if (s0<s4) {s0,s4}={s4,s0}; if (s0<s5) {s0,s5}={s5,s0}; if (s0<t0) {s0,t0}={t0,s0};
      if (s1<s2) {s1,s2}={s2,s1}; if (s1<s3) {s1,s3}={s3,s1}; if (s1<s4) {s1,s4}={s4,s1}; if (s1<s5) {s1,s5}={s5,s1}; if (s1<t0) {s1,t0}={t0,s1};
      if (s2<s3) {s2,s3}={s3,s2}; if (s2<s4) {s2,s4}={s4,s2}; if (s2<s5) {s2,s5}={s5,s2}; if (s2<t0) {s2,t0}={t0,s2};
      if (s3<s4) {s3,s4}={s4,s3}; if (s3<s5) {s3,s5}={s5,s3}; if (s3<t0) {s3,t0}={t0,s3};
      if (s4<s5) {s4,s5}={s5,s4}; if (s4<t0) {s4,t0}={t0,s4};
      if (s5<t0) {s5,t0}={t0,s5};
      y <= {8'b0, s3};
      w5<=w4; w4<=w3; w3<=w2; w2<=w1; w1<=w0; w0<=x;
    end
  end
endmodule