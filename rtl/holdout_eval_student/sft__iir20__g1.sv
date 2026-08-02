module sft__iir20__g1 (
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
  wire [31:0] acc = 3*x + r1 + ((9*y)>>4) + ((5*y2)>>4);
  always @(posedge clk) begin
    if (!rst_n) begin
      y <= 0;
      y2 <= 0;
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
      r20 <= 0;
    end else begin
      y <= acc[15:0];
      y2 <= y;
      r1 <= (5*x + r2) & 16'hffff;
      r2 <= (7*x + r3) & 16'hffff;
      r3 <= (9*x + r4) & 16'hffff;
      r4 <= (11*x + r5) & 16'hffff;
      r5 <= (13*x + r6) & 16'hffff;
      r6 <= (15*x + r7) & 16'hffff;
      r7 <= (17*x + r8) & 16'hffff;
      r8 <= (19*x + r9) & 16'hffff;
      r9 <= (21*x + r10) & 16'hffff;
      r10 <= (23*x + r11) & 16'hffff;
      r11 <= (25*x + r12) & 16'hffff;
      r12 <= (27*x + r13) & 16'hffff;
      r13 <= (29*x + r14) & 16'hffff;
      r14 <= (31*x + r15) & 16'hffff;
      r15 <= (33*x + r16) & 16'hffff;
      r16 <= (35*x + r17) & 16'hffff;
      r17 <= (37*x + r18) & 16'hffff;
      r18 <= (39*x + r19) & 16'hffff;
      r19 <= (41*x + r20) & 16'hffff;
      r20 <= (43*x) & 16'hffff;
    end
  end
endmodule