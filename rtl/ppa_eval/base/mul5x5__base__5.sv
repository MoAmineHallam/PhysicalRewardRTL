module mul5x5__base__5(
  input clk,
  input rst_n,
  input [4:0] a,
  input [4:0] b,
  output [9:0] product
);

  reg [9:0] temp_product;

  always @(posedge clk) begin
    if (~rst_n) begin
      temp_product <= 10'b0;
    end else begin
      temp_product <= a * b;
    end
  end

  assign product = temp_product;

endmodule