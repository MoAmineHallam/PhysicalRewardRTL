module sft__iir5__g8 (
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);
  reg [15:0] t0;
  reg [15:0] t1;
  reg [15:0] t2;
  reg [15:0] t3;
  reg [15:0] t4;
  reg [15:0] t5;
  reg [15:0] y2;
  wire [31:0] acc = 3*x + t0 + ((9*y)>>4) + ((5*y2)>>4);
  always @(posedge clk) begin
    if (!rst_n) begin y<=0; y2<=0; t0<=0; t1<=0; t2<=0; t3<=0; t4<=0; t5<=0; end
    else begin
      y <= acc[15:0];
      y2 <= y;
      t0<=5*x + t1;
      t1<=7*x + t2;
      t2<=9*x + t3;
      t3<=11*x + t4;
      t4<=13*x + t5;
      t5<=0;
    end
  end
endmodule