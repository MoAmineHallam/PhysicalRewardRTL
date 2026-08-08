module grpo__iir20__g6 (
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);
  reg [15:0] r1;
  reg [15:0] r2;
  reg [15:0] r3;
  reg [15:0] r4;
  reg [15:0] r5;
  reg [15:0] r6;
  reg [15:0] r7;
  reg [15:0] r8;
  reg [15:0] r9;
  reg [15:0] r10;
  reg [15:0] r11;
  reg [15:0] r12;
  reg [15:0] r13;
  reg [15:0] r14;
  reg [15:0] r15;
  reg [15:0] r16;
  reg [15:0] r17;
  reg [15:0] r18;
  reg [15:0] r19;
  reg [15:0] r20;
  reg [15:0] y2;
  wire [31:0] t0 = 3*x;
  wire [31:0] t1 = t0 + 5*r1;
  wire [31:0] t2 = t1 + 7*r2;
  wire [31:0] t3 = t2 + 9*r3;
  wire [31:0] t4 = t3 + 11*r4;
  wire [31:0] t5 = t4 + 13*r5;
  wire [31:0] t6 = t5 + 15*r6;
  wire [31:0] t7 = t6 + 17*r7;
  wire [31:0] t8 = t7 + 19*r8;
  wire [31:0] t9 = t8 + 21*r9;
  wire [31:0] t10 = t9 + 23*r10;
  wire [31:0] t11 = t10 + 25*r11;
  wire [31:0] t12 = t11 + 27*r12;
  wire [31:0] t13 = t12 + 29*r13;
  wire [31:0] t14 = t13 + 31*r14;
  wire [31:0] t15 = t14 + 33*r15;
  wire [31:0] t16 = t15 + 35*r16;
  wire [31:0] t17 = t16 + 37*r17;
  wire [31:0] t18 = t17 + 39*r18;
  wire [31:0] t19 = t18 + 41*r19;
  wire [31:0] t20 = t19 + 43*r20 + ((9*y)>>4) + ((5*y2)>>4);
  always @(posedge clk) begin
    if (!rst_n) begin y<=0; y2<=0; r1<=0; r2<=0; r3<=0; r4<=0; r5<=0; r6<=0; r7<=0; r8<=0; r9<=0; r10<=0; r11<=0; r12<=0; r13<=0; r14<=0; r15<=0; r16<=0; r17<=0; r18<=0; r19<=0; r20<=0; end
    else begin
      y <= t20[15:0];
      y2 <= y;
      r1 <= x;
      r2 <= r1;
      r3 <= r2;
      r4 <= r3;
      r5 <= r4;
      r6 <= r5;
      r7 <= r6;
      r8 <= r7;
      r9 <= r8;
      r10 <= r9;
      r11 <= r10;
      r12 <= r11;
      r13 <= r12;
      r14 <= r13;
      r15 <= r14;
      r16 <= r15;
      r17 <= r16;
      r18 <= r17;
      r19 <= r18;
      r20 <= r19;
    end
  end
endmodule