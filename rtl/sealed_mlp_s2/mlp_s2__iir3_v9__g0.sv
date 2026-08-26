module mlp_s2__iir3_v9__g0 (
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);
  reg [15:0] r1;
  reg [15:0] r2;
  reg [15:0] r3;
  reg [15:0] y2;
  wire [31:0] acc = 37*x + r1 + ((9*y)>>4) + ((5*y2)>>4);
  always @(posedge clk) begin
    if (!rst_n) begin
      r1 <= 16'd0;
      r2 <= 16'd0;
      r3 <= 16'd0;
      y2 <= 16'd0;
      y <= 16'd0;
    end else begin
      r1 <= (62*x + r2) & 16'hFFFF;
      r2 <= (53*x + r3) & 16'hFFFF;
      r3 <= (36*x) & 16'hFFFF;
      y2 <= y;
      y <= acc[15:0];
    end
  end
endmodule
