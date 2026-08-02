module grpo__iir9__g8 (
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);
  reg [15:0] rd1;
  reg [15:0] rd2;
  reg [15:0] rd3;
  reg [15:0] rd4;
  reg [15:0] rd5;
  reg [15:0] rd6;
  reg [15:0] rd7;
  reg [15:0] rd8;
  reg [15:0] rd9;
  reg [15:0] y2;
  wire [31:0] acc = 3*x + rd1 + ((9*y)>>4) + ((5*y2)>>4);
  always @(posedge clk) begin
    if (!rst_n) begin
      y <= 0;
      y2 <= 0;
      rd1 <= 0;
      rd2 <= 0;
      rd3 <= 0;
      rd4 <= 0;
      rd5 <= 0;
      rd6 <= 0;
      rd7 <= 0;
      rd8 <= 0;
      rd9 <= 0;
    end else begin
      y <= acc[15:0];
      y2 <= y;
      rd1 <= (5*x + rd2) & 16'hFFFF;
      rd2 <= (7*x + rd3) & 16'hFFFF;
      rd3 <= (9*x + rd4) & 16'hFFFF;
      rd4 <= (11*x + rd5) & 16'hFFFF;
      rd5 <= (13*x + rd6) & 16'hFFFF;
      rd6 <= (15*x + rd7) & 16'hFFFF;
      rd7 <= (17*x + rd8) & 16'hFFFF;
      rd8 <= (19*x + rd9) & 16'hFFFF;
      rd9 <= (21*x) & 16'hFFFF;
    end
  end
endmodule