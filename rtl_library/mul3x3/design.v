// 3x3 unsigned multiplier (registered).
module mul3x3 (
    input  wire clk,
    input  wire rst_n,
    input  wire [2:0] a,
    input  wire [2:0] b,
    output reg  [5:0] product
);
    always @(posedge clk) begin
        if (!rst_n) product <= 6'd0;
        else        product <= a * b;
    end
endmodule
