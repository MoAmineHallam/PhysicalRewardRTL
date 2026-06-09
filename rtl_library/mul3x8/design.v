// 3x8 unsigned multiplier (registered).
module mul3x8 (
    input  wire clk,
    input  wire rst_n,
    input  wire [2:0] a,
    input  wire [7:0] b,
    output reg  [10:0] product
);
    always @(posedge clk) begin
        if (!rst_n) product <= 11'd0;
        else        product <= a * b;
    end
endmodule
