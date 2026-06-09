// 2x8 unsigned multiplier (registered).
module mul2x8 (
    input  wire clk,
    input  wire rst_n,
    input  wire [1:0] a,
    input  wire [7:0] b,
    output reg  [9:0] product
);
    always @(posedge clk) begin
        if (!rst_n) product <= 10'd0;
        else        product <= a * b;
    end
endmodule
