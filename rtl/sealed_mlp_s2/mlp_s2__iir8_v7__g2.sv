module mlp_s2__iir8_v7__g2 (
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
  wire [31:0] acc = 57 * x + r1 + ((9 * y) >> 4) + ((5 * y2) >> 4);
  always @(posedge clk) begin
    if (!rst_n) begin
      r1 <= 16'd0;
      r2 <= 16'd0;
      r3 <= 16'd0;
      r4 <= 16'd0;
      r5 <= 16'd0;
      r6 <= 16'd0;
      r7 <= 16'd0;
      r8 <= 16'd0;
      y2 <= 16'd0;
      y <= 16'd0;
    end else begin
      r1 <= (40 * x + r2) & 16'hFFFF;
      r2 <= (15 * x + r3) & 16'hFFFF;
      r3 <= (4 * x + r4) & 16'hFFFF;
      r4 <= (33 * x + r5) & 16'hFFFF;
      r5 <= (61 * x + r6) & 16'hFFFF;
      r6 <= (39 * x + r7) & 16'hFFFF;
      r7 <= (57 * x + r8) & 16'hFFFF;
      r8 <= (30 * x) & 16'hFFFF;
      y2 <= y;
      y <= acc[15:0];
    end
  end
endmodule
