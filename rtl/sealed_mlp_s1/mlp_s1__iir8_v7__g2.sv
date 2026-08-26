module mlp_s1__iir8_v7__g2 (
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
  reg [15:0] y2;
  wire [31:0] acc = 57*x + 40*r1 + 15*r2 + 4*r3 + 33*r4 + 61*r5 + 39*r6 + 57*r7 + 30*r8 + ((9*y)>>4) + ((5*y2)>>4);
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
      y <= acc[15:0];
      y2 <= y;
    end
  end
endmodule
