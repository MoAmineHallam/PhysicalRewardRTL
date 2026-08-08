module grpo__iir5_v1__g1 (
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);
  reg [7:0] x_d1;
  reg [7:0] x_d2;
  reg [7:0] x_d3;
  reg [7:0] x_d4;
  reg [7:0] x_d5;
  reg [15:0] y2;
  wire [31:0] acc = 23*x + 5*x_d1 + 53*x_d2 + 56*x_d3 + 8*x_d4 + 27*x_d5 + ((9*y)>>4) + ((5*y2)>>4);
  always @(posedge clk) begin
    if (!rst_n) begin y<=0; y2<=0; x_d1<=0; x_d2<=0; x_d3<=0; x_d4<=0; x_d5<=0; end
    else begin
      y <= acc[15:0];
      y2 <= y;
      x_d1 <= x;
      x_d2 <= x_d1;
      x_d3 <= x_d2;
      x_d4 <= x_d3;
      x_d5 <= x_d4;
    end
  end
endmodule