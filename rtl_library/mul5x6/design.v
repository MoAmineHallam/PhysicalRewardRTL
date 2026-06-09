// 5x6 unsigned multiplier (registered).
module mul5x6 (
    input  wire clk,
    input  wire rst_n,
    input  wire [4:0] a,
    input  wire [5:0] b,
    output reg  [10:0] product
);
    always @(posedge clk) begin
        if (!rst_n) product <= 11'd0;
        else        product <= a * b;
    end
endmodule
