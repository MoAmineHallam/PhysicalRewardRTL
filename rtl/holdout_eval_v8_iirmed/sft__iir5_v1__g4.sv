module sft__iir5_v1__g4 (
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);
  reg [15:0] w0;
  reg [15:0] w1;
  reg [15:0] w2;
  reg [15:0] w3;
  reg [15:0] w4;
  reg [15:0] w5;
  reg [15:0] y2;
  wire [31:0] acc = 23*x + w0 + ((9*y)>>4) + ((5*y2)>>4);
  always @(posedge clk) begin
    if (!rst_n) begin y<=0; y2<=0; w0<=0; w1<=0; w2<=0; w3<=0; w4<=0; w5<=0; end
    else begin
      y <= acc[15:0];
      y2 <= y;
      w0 <= (5*x + w1) & 16'hFFFF;
      w1 <= (53*x + w2) & 16'hFFFF;
      w2 <= (56*x + w3) & 16'hFFFF;
      w3 <= (8*x + w4) & 16'hFFFF;
      w4 <= (27*x + w5) & 16'hFFFF;
      w5 <= (0*x) & 16'hFFFF;
    end
  end
endmodule