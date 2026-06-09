// 8x2 unsigned multiplier (registered).
module mul8x2 (
    input  wire clk,
    input  wire rst_n,
    input  wire [7:0] a,
    input  wire [1:0] b,
    output reg  [9:0] product
);
    always @(posedge clk) begin
        if (!rst_n) product <= 10'd0;
        else        product <= a * b;
    end
endmodule
