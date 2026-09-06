module rf_s4__iir18_v7__g0 (
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
  reg [15:0] y2;
  wire [31:0] acc = 25*x + r1 + ((9*y)>>4) + ((5*y2)>>4);
  always @(posedge clk) begin
    if (!rst_n) begin y<=0; y2<=0; r1<=0; r2<=0; r3<=0; r4<=0; r5<=0; r6<=0; r7<=0; r8<=0; r9<=0; r10<=0; r11<=0; r12<=0; r13<=0; r14<=0; r15<=0; r16<=0; r17<=0; r18<=0; end
    else begin
      y <= acc[15:0];
      y2 <= y;
      r1 <= (26*x + r2) & 16'hFFFF;
      r2 <= (46*x + r3) & 16'hFFFF;
      r3 <= (49*x + r4) & 16'hFFFF;
      r4 <= (16*x + r5) & 16'hFFFF;
      r5 <= (8*x + r6) & 16'hFFFF;
      r6 <= (15*x + r7) & 16'hFFFF;
      r7 <= (31*x + r8) & 16'hFFFF;
      r8 <= (37*x + r9) & 16'hFFFF;
      r9 <= (52*x + r10) & 16'hFFFF;
      r10 <= (6*x + r11) & 16'hFFFF;
      r11 <= (54*x + r12) & 16'hFFFF;
      r12 <= (60*x + r13) & 16'hFFFF;
      r13 <= (33*x + r14) & 16'hFFFF;
      r14 <= (33*x + r15) & 16'hFFFF;
      r15 <= (62*x + r16) & 16'hFFFF;
      r16 <= (48*x + r17) & 16'hFFFF;
      r17 <= (18*x + r18) & 16'hFFFF;
      r18 <= (56*x) & 16'hFFFF;
    end
  end
endmodule
