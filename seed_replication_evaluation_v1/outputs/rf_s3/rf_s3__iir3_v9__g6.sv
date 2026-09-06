module rf_s3__iir3_v9__g6 (
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);
  reg [15:0] r1;
  reg [15:0] r2;
  reg [15:0] r3;
  reg [15:0] y2;
  always @(posedge clk) begin
    if (!rst_n) begin y<=0; y2<=0; r1<=0; r2<=0; r3<=0; end
    else begin
      y <= ((16'd37*x + r1 + ((9*y)>>4) + ((5*y2)>>4)) & 16'hFFFF);
      r1 <= (16'd62*x + r2) & 16'hFFFF;
      r2 <= (16'd53*x + r3) & 16'hFFFF;
      r3 <= (16'd36*x) & 16'hFFFF;
      y2 <= y;
    end
  end
endmodule
