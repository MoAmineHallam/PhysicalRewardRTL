// 2x4 unsigned multiplier (registered).
module mul2x4 (
    input  wire clk,
    input  wire rst_n,
    input  wire [1:0] a,
    input  wire [3:0] b,
    output reg  [5:0] product
);
    always @(posedge clk) begin
        if (!rst_n) product <= 6'd0;
        else        product <= a * b;
    end
endmodule
