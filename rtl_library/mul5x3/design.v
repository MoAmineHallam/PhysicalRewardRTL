// 5x3 unsigned multiplier (registered).
module mul5x3 (
    input  wire clk,
    input  wire rst_n,
    input  wire [4:0] a,
    input  wire [2:0] b,
    output reg  [7:0] product
);
    always @(posedge clk) begin
        if (!rst_n) product <= 8'd0;
        else        product <= a * b;
    end
endmodule
