module mlp_s2__iir24_v2__g4 (
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
      r1<=16'd0;
      r2<=16'd0;
      r3<=16'd0;
      r4<=16'd0;
      r5<=16'd0;
      r6<=16'd0;
      r7<=16'd0;
      r8<=16'd0;
      r9<=16'd0;
      r10<=16'd0;
      r11<=16'd0;
      r12<=16'd0;
      r13<=16'd0;
      r14<=16'd0;
      r15<=16'd0;
      r16<=16'd0;
      r17<=16'd0;
      r18<=16'd0;
      r19<=16'd0;
      r20<=16'd0;
      r21<=16'd0;
      r22<=16'd0;
      r23<=16'd0;
      r24<=16'd0;
      y<=16'd0;
      y2<=16'd0;
    end else begin
      r1<=16'd15*x + r2;
      r2<=16'd4*x + r3;
      r3<=16'd35*x + r4;
      r4<=16'd41*x + r5;
      r5<=16'd47*x + r6;
      r6<=16'd40*x + r7;
      r7<=16'd2*x + r8;
      r8<=16'd60*x + r9;
      r9<=16'd19*x + r10;
      r10<=16'd5*x + r11;
      r11<=16'd12*x + r12;
      r12<=16'd50*x + r13;
      r13<=16'd28*x + r14;
      r14<=16'd46*x + r15;
      r15<=16'd49*x + r16;
      r16<=16'd15*x + r17;
      r17<=16'd22*x + r18;
      r18<=16'd36*x + r19;
      r19<=16'd52*x + r20;
      r20<=16'd8*x + r21;
      r21<=16'd31*x + r22;
      r22<=16'd50*x + r23;
      r23<=16'd57*x + r24;
      r24<=16'd45*x;
      y <= acc[15:0];
      y2 <= y;
    end
  end
endmodule
