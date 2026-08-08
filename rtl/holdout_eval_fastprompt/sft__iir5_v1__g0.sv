module sft__iir5_v1__g0 (
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);
  reg [7:0] xd0;
  reg [7:0] xd1;
  reg [7:0] xd2;
  reg [7:0] xd3;
  reg [7:0] xd4;
  reg [15:0] y2;
  reg [15:0] y3;
  reg [15:0] y4;
  reg [15:0] y5;
  wire [31:0] acc = 23*x + 5*xd0 + 53*xd1 + 56*xd2 + 8*xd3 + 27*xd4 + ((9*y)>>4) + ((5*y2)>>4);
  always @(posedge clk) begin
    if (!rst_n) begin
      xd0 <= 8'd0; xd1 <= 8'd0; xd2 <= 8'd0; xd3 <= 8'd0; xd4 <= 8'd0;
      y <= 16'd0; y2 <= 16'd0; y3 <= 16'd0; y4 <= 16'd0; y5 <= 16'd0;
    end else begin
      xd0 <= x; xd1 <= xd0; xd2 <= xd1; xd3 <= xd2; xd4 <= xd3;
      y5 <= y4; y4 <= y3; y3 <= y2; y2 <= y; y <= acc[15:0];
    end
  end
endmodule