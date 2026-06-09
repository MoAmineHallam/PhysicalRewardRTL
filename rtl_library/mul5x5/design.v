// 5x5 unsigned multiplier (registered).
module mul5x5 (
    input  wire clk,
    input  wire rst_n,
    input  wire [4:0] a,
    input  wire [4:0] b,
    output reg  [9:0] product
);
    always @(posedge clk) begin
        if (!rst_n) product <= 10'd0;
        else        product <= a * b;
    end
endmodule
