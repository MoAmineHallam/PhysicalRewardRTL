// 5x4 unsigned multiplier (registered).
module mul5x4 (
    input  wire clk,
    input  wire rst_n,
    input  wire [4:0] a,
    input  wire [3:0] b,
    output reg  [8:0] product
);
    always @(posedge clk) begin
        if (!rst_n) product <= 9'd0;
        else        product <= a * b;
    end
endmodule
