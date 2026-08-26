module mlp_s1__iir18_v7__g0 (
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
  wire [31:0] acc = 25*x + 26*r1 + 46*r2 + 49*r3 + 16*r4 + 8*r5 + 15*r6 + 31*r7 + 37*r8 + 52*r9 + 6*r10 + 54*r11 + 60*r12 + 33*r13 + 33*r14 + 62*r15 + 48*r16 + 18*r17 + 56*r18 + ((9*y)>>4) + ((5*y2)>>4);
  always @(posedge clk) begin
    if (!rst_n) begin
      r1 <= 0;
      r2 <= 0;
      r3 <= 0;
      r4 <= 0;
      r5 <= 0;
      r6 <= 0;
      r7 <= 0;
      r8 <= 0;
      r9 <= 0;
      r10 <= 0;
      r11 <= 0;
      r12 <= 0;
      r13 <= 0;
      r14 <= 0;
      r15 <= 0;
      r16 <= 0;
      r17 <= 0;
      r18 <= 0;
      y <= 0;
      y2 <= 0;
    end else begin
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
      y <= acc[15:0];
      y2 <= y;
    end
  end
endmodule
