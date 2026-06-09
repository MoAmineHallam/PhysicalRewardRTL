// 2x7 unsigned multiplier (registered).
module mul2x7 (
    input  wire clk,
    input  wire rst_n,
    input  wire [1:0] a,
    input  wire [6:0] b,
    output reg  [8:0] product
);
    always @(posedge clk) begin
        if (!rst_n) product <= 9'd0;
        else        product <= a * b;
    end
endmodule
