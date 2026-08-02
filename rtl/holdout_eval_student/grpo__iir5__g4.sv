module grpo__iir5__g4 (
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);
  reg [15:0] r0;
  reg [15:0] r1;
  reg [15:0] r2;
  reg [15:0] r3;
  reg [15:0] r4;
  reg [15:0] r5;
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
    end else begin
      y <= acc[15:0];
      y2 <= y;
      r0 <= 5*x + r1;
      r1 <= 7*x + r2;
      r2 <= 9*x + r3;
      r3 <= 11*x + r4;
      r4 <= 13*x + r5;
      r5 <= 0;
    end
  end
endmodule