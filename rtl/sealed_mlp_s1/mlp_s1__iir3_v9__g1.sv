module mlp_s1__iir3_v9__g1 (
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);
  reg [15:0] r1;
  reg [15:0] r2;
  reg [15:0] r3;
  reg [15:0] y2;
  wire [31:0] acc = 37*x + 62*r1 + 53*r2 + 36*r3 + ((9*y)>>4) + ((5*y2)>>4);
  always @(posedge clk) begin
    if (!rst_n) begin
      r1 <= 0;
      r2 <= 0;
      r3 <= 0;
      y <= 0;
      y2 <= 0;
    end else begin
      r1 <= x;
      r2 <= r1;
      r3 <= r2;
      y <= acc[15:0];
      y2 <= y;
    end
  end
endmodule
