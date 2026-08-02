module grpo__iir20__g5 (
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);
  reg [15:0] r0;
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
  reg [15:0] y2;
  wire [31:0] acc = 3*x + r0 + ((9*y)>>4) + ((5*y2)>>4);
  always @(posedge clk) begin
    if (!rst_n) begin
      y <= 0;
      y2 <= 0;
      r0 <= 0;
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
      r19 <= 0;
    end else begin
      y <= acc[15:0];
      y2 <= y;
      r0 <= (5*x + r1) & 16'hFFFF;
      r1 <= (7*x + r2) & 16'hFFFF;
      r2 <= (9*x + r3) & 16'hFFFF;
      r3 <= (11*x + r4) & 16'hFFFF;
      r4 <= (13*x + r5) & 16'hFFFF;
      r5 <= (15*x + r6) & 16'hFFFF;
      r6 <= (17*x + r7) & 16'hFFFF;
      r7 <= (19*x + r8) & 16'hFFFF;
      r8 <= (21*x + r9) & 16'hFFFF;
      r9 <= (23*x + r10) & 16'hFFFF;
      r10 <= (25*x + r11) & 16'hFFFF;
      r11 <= (27*x + r12) & 16'hFFFF;
      r12 <= (29*x + r13) & 16'hFFFF;
      r13 <= (31*x + r14) & 16'hFFFF;
      r14 <= (33*x + r15) & 16'hFFFF;
      r15 <= (35*x + r16) & 16'hFFFF;
      r16 <= (37*x + r17) & 16'hFFFF;
      r17 <= (39*x + r18) & 16'hFFFF;
      r18 <= (41*x + r19) & 16'hFFFF;
      r19 <= (43*x) & 16'hFFFF;
    end
  end
endmodule