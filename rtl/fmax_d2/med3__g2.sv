module med3__g2 (
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);
  reg [7:0] w0;
  reg [7:0] w1;
  wire [7:0] l0_0 = x;
  wire [7:0] l0_1 = w0;
  wire [7:0] l0_2 = w1;
  wire [7:0] l1_0 = (l0_0 <= l0_1) ? l0_0 : l0_1;
  wire [7:0] l1_1 = (l0_0 <= l0_1) ? l0_1 : l0_0;
  wire [7:0] l1_2 = l0_2;
  wire [7:0] l2_1 = (l1_1 <= l1_2) ? l1_1 : l1_2;
  wire [7:0] l2_2 = (l1_1 <= l1_2) ? l1_2 : l1_1;
  wire [7:0] l2_0 = l1_0;
  reg [7:0] s0_0;
  reg [7:0] s0_1;
  reg [7:0] s0_2;
  wire [7:0] l3_0 = (s0_0 <= s0_1) ? s0_0 : s0_1;
  wire [7:0] l3_1 = (s0_0 <= s0_1) ? s0_1 : s0_0;
  wire [7:0] l3_2 = s0_2;
  always @(posedge clk) begin
    if (!rst_n) begin
      y<=0; w0<=0; w1<=0;
      s0_0<=0; s0_1<=0; s0_2<=0;
    end else begin
      y <= {8'b0, l3_1};
      s0_0<=l2_0; s0_1<=l2_1; s0_2<=l2_2;
      w1<=w0; w0<=x;
    end
  end
endmodule