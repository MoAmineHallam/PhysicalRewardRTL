// Order-12 IIR, TRANSPOSED feedforward chain: one multiply+add per stage
// (registered partial sums) + a tiny feedback stage -> critical path roughly
// independent of the order -> high Fmax. Same function as the direct form.
module iir12__v1 (
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);
  reg [15:0] r1;
  reg [15:0] r2;
  reg [15:0] r3;
  reg [15:0] r4;
  reg [15:0] r5;
  reg [15:0] r6;
  reg [15:0] r7;
  reg [15:0] r8;
  reg [15:0] r9;
  reg [15:0] r10;
  reg [15:0] r11;
  reg [15:0] r12;
  reg [15:0] y2;
  wire [31:0] acc = 3*x + r1 + ((9*y)>>4) + ((5*y2)>>4);
  always @(posedge clk) begin
    if (!rst_n) begin y<=0; y2<=0; r1<=0; r2<=0; r3<=0; r4<=0; r5<=0; r6<=0; r7<=0; r8<=0; r9<=0; r10<=0; r11<=0; r12<=0; end
    else begin
      y <= acc[15:0];
      y2 <= y;
      r1 <= (5*x + r2) & 16'hFFFF;
      r2 <= (7*x + r3) & 16'hFFFF;
      r3 <= (9*x + r4) & 16'hFFFF;
      r4 <= (11*x + r5) & 16'hFFFF;
      r5 <= (13*x + r6) & 16'hFFFF;
      r6 <= (15*x + r7) & 16'hFFFF;
      r7 <= (17*x + r8) & 16'hFFFF;
      r8 <= (19*x + r9) & 16'hFFFF;
      r9 <= (21*x + r10) & 16'hFFFF;
      r10 <= (23*x + r11) & 16'hFFFF;
      r11 <= (25*x + r12) & 16'hFFFF;
      r12 <= (27*x) & 16'hFFFF;
    end
  end
endmodule
