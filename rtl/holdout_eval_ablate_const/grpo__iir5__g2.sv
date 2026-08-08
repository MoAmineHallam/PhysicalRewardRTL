module grpo__iir5__g2 (
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);
  reg [7:0] xd1;
  reg [7:0] xd2;
  reg [7:0] xd3;
  reg [7:0] xd4;
  reg [7:0] xd5;
  reg [15:0] y2;
  wire [31:0] acc = 3*x + 5*xd1 + 7*xd2 + 9*xd3 + 11*xd4 + 13*xd5 + ((9*y)>>4) + ((5*y2)>>4);
  always @(posedge clk) begin
    if (!rst_n) begin
      xd1 <= 8'd0; xd2 <= 8'd0; xd3 <= 8'd0; xd4 <= 8'd0; xd5 <= 8'd0; y <= 16'd0; y2 <= 16'd0;
    end else begin
      xd1 <= x; xd2 <= xd1; xd3 <= xd2; xd4 <= xd3; xd5 <= xd4;
      y <= acc[15:0];
      y2 <= y;
    end
  end
endmodule