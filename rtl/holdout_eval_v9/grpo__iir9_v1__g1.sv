module grpo__iir9_v1__g1 (
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
  reg [15:0] y2;
  wire [31:0] acc = 2*x + r1 + ((9*y)>>4) + ((5*y2)>>4);
  always @(posedge clk) begin
    if (!rst_n) begin r1 <= 16'd0; r2 <= 16'd0; r3 <= 16'd0; r4 <= 16'd0; r5 <= 16'd0; r6 <= 16'd0; r7 <= 16'd0; r8 <= 16'd0; r9 <= 16'd0; y <= 16'd0; y2 <= 16'd0; end
    else begin
      r1 <= 29*x + r2;
      r2 <= 34*x + r3;
      r3 <= 29*x + r4;
      r4 <= 13*x + r5;
      r5 <= 18*x + r6;
      r6 <= 60*x + r7;
      r7 <= 33*x + r8;
      r8 <= 62*x + r9;
      r9 <= 10*x;
      y <= acc[15:0];
      y2 <= y;
    end
  end
endmodule