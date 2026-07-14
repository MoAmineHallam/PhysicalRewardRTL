module med5 (
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);
  reg [7:0] w0;
  reg [7:0] w1;
  reg [7:0] w2;
  reg [7:0] w3;
  wire [7:0] l0_0 = x;
  wire [7:0] l0_1 = w0;
  wire [7:0] l0_2 = w1;
  wire [7:0] l0_3 = w2;
  wire [7:0] l0_4 = w3;
  wire [7:0] l1_0 = (l0_0 <= l0_1) ? l0_0 : l0_1;
  wire [7:0] l1_1 = (l0_0 <= l0_1) ? l0_1 : l0_0;
  wire [7:0] l1_2 = (l0_2 <= l0_3) ? l0_2 : l0_3;
  wire [7:0] l1_3 = (l0_2 <= l0_3) ? l0_3 : l0_2;
  wire [7:0] l1_4 = l0_4;
  wire [7:0] l2_1 = (l1_1 <= l1_2) ? l1_1 : l1_2;
  wire [7:0] l2_2 = (l1_1 <= l1_2) ? l1_2 : l1_1;
  wire [7:0] l2_3 = (l1_3 <= l1_4) ? l1_3 : l1_4;
  wire [7:0] l2_4 = (l1_3 <= l1_4) ? l1_4 : l1_3;
  wire [7:0] l2_0 = l1_0;
  wire [7:0] l3_0 = (l2_0 <= l2_1) ? l2_0 : l2_1;
  wire [7:0] l3_1 = (l2_0 <= l2_1) ? l2_1 : l2_0;
  wire [7:0] l3_2 = (l2_2 <= l2_3) ? l2_2 : l2_3;
  wire [7:0] l3_3 = (l2_2 <= l2_3) ? l2_3 : l2_2;
  wire [7:0] l3_4 = l2_4;
  wire [7:0] l4_1 = (l3_1 <= l3_2) ? l3_1 : l3_2;
  wire [7:0] l4_2 = (l3_1 <= l3_2) ? l3_2 : l3_1;
  wire [7:0] l4_3 = (l3_3 <= l3_4) ? l3_3 : l3_4;
  wire [7:0] l4_4 = (l3_3 <= l3_4) ? l3_4 : l3_3;
  wire [7:0] l4_0 = l3_0;
  wire [7:0] l5_0 = (l4_0 <= l4_1) ? l4_0 : l4_1;
  wire [7:0] l5_1 = (l4_0 <= l4_1) ? l4_1 : l4_0;
  wire [7:0] l5_2 = (l4_2 <= l4_3) ? l4_2 : l4_3;
  wire [7:0] l5_3 = (l4_2 <= l4_3) ? l4_3 : l4_2;
  wire [7:0] l5_4 = l4_4;
  always @(posedge clk) begin
    if (!rst_n) begin
      y<=0; w0<=0; w1<=0; w2<=0; w3<=0;
    end else begin
      y <= {8'b0, l5_2};
      w3<=w2; w2<=w1; w1<=w0; w0<=x;
    end
  end
endmodule
