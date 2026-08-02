module grpo__iir9__g12 (
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
  reg [15:0] y1;
  wire [31:0] acc = 3*x + r1 + ((9*y)>>4) + ((5*y1)>>4);
  always @(posedge clk) begin
    if (!rst_n) begin
      y <= 0;
      y1 <= 0;
      r1 <= 0;
      r2 <= 0;
      r3 <= 0;
      r4 <= 0;
      r5 <= 0;
      r6 <= 0;
      r7 <= 0;
      r8 <= 0;
      r9 <= 0;
    end else begin
      y <= acc[15:0];
      y1 <= y;
      r1 <= (5*x + r2) & (2**16-1);
      r2 <= (7*x + r3) & (2**16-1);
      r3 <= (9*x + r4) & (2**16-1);
      r4 <= (11*x + r5) & (2**16-1);
      r5 <= (13*x + r6) & (2**16-1);
      r6 <= (15*x + r7) & (2**16-1);
      r7 <= (17*x + r8) & (2**16-1);
      r8 <= (19*x + r9) & (2**16-1);
      r9 <= (21*x) & (2**16-1);
    end
  end
endmodule