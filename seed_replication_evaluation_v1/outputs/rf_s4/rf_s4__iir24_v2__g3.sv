module rf_s4__iir24_v2__g3 (
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
  wire [31:0] acc = 63*x + r1 + ((9*y)>>4) + ((5*y2)>>4);
  always @(posedge clk) begin
    if (!rst_n) begin
      y<=0; y2<=0; r1<=0; r2<=0; r3<=0; r4<=0; r5<=0; r6<=0; r7<=0; r8<=0; r9<=0; r10<=0; r11<=0; r12<=0; r13<=0; r14<=0; r15<=0; r16<=0; r17<=0; r18<=0; r19<=0; r20<=0; r21<=0; r22<=0; r23<=0; r24<=0;
    end else begin
      y<=acc[15:0];
      y2<=y;
      r1<=15*x + r2;
      r2<=4*x + r3;
      r3<=35*x + r4;
      r4<=41*x + r5;
      r5<=47*x + r6;
      r6<=40*x + r7;
      r7<=2*x + r8;
      r8<=60*x + r9;
      r9<=19*x + r10;
      r10<=5*x + r11;
      r11<=12*x + r12;
      r12<=50*x + r13;
      r13<=28*x + r14;
      r14<=46*x + r15;
      r15<=49*x + r16;
      r16<=15*x + r17;
      r17<=22*x + r18;
      r18<=36*x + r19;
      r19<=52*x + r20;
      r20<=8*x + r21;
      r21<=31*x + r22;
      r22<=50*x + r23;
      r23<=57*x + r24;
      r24<=45*x;
    end
  end
endmodule
