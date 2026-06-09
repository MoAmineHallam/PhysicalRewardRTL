// 5x8 unsigned multiplier (registered).
module mul5x8 (
    input  wire clk,
    input  wire rst_n,
    input  wire [4:0] a,
    input  wire [7:0] b,
    output reg  [12:0] product
);
    always @(posedge clk) begin
        if (!rst_n) product <= 13'd0;
        else        product <= a * b;
    end
endmodule
