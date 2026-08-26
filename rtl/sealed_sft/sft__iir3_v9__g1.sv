module sft__iir3_v9__g1 (
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);
  reg [7:0] xd1;
  reg [7:0] xd2;
  reg [7:0] xd3;
  reg [15:0] y2;
  wire [31:0] acc = 37*x + 62*xd1 + 53*xd2 + 36*xd3 + ((9*y)>>4) + ((5*y2)>>4);
  always @(posedge clk) begin
    if (!rst_n) begin y<=0; y2<=0; xd1<=0; xd2<=0; xd3<=0; end
    else begin
      y <= acc[15:0];
      y2 <= y;
      xd3<=xd2; xd2<=xd1; xd1 <= x;
    end
  end
endmodule
