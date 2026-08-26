module rf_s1__iir3_v9__g0 (
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);
  reg [15:0] r1, r2, r3;
  reg [15:0] y2;
  wire [31:0] acc = 37*x + r1 + ((9*y)>>4) + ((5*y2)>>4);
  always @(posedge clk) begin
    if (!rst_n) begin y<=0; y2<=0; r1<=0; r2<=0; r3<=0; end
    else begin
      y <= acc[15:0];
      y2 <= y;
      r1 <= (62*x + r2) & 16'hFFFF;
      r2 <= (53*x + r3) & 16'hFFFF;
      r3 <= (36*x) & 16'hFFFF;
    end
  end
endmodule
