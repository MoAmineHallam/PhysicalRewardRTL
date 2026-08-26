module sft__iir24_v2__g5 (
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
  reg [15:0] r21;
  reg [15:0] r22;
  reg [15:0] r23;
  reg [15:0] r24;
  reg [15:0] y2;
  wire [31:0] acc = 63*x + 15*r1 + 4*r2 + 35*r3 + 41*r4 + 47*r5 + 40*r6 + 2*r7 + 60*r8 + 19*r9 + 5*r10 + 12*r11 + 50*r12 + 28*r13 + 46*r14 + 49*r15 + 15*r16 + 22*r17 + 36*r18 + 52*r19 + 8*r20 + 31*r21 + 50*r22 + 57*r23 + 45*r24 + ((9*y)>>4) + ((5*y2)>>4);
  always @(posedge clk) begin
    if (!rst_n) begin y<=0; y2<=0; r1<=0; r2<=0; r3<=0; r4<=0; r5<=0; r6<=0; r7<=0; r8<=0; r9<=0; r10<=0; r11<=0; r12<=0; r13<=0; r14<=0; r15<=0; r16<=0; r17<=0; r18<=0; r19<=0; r20<=0; r21<=0; r22<=0; r23<=0; r24<=0; end
    else begin
      y <= acc[15:0];
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
      r21 <= r20;
      r22 <= r21;
      r23 <= r22;
      r24 <= r23;
    end
  end
endmodule
