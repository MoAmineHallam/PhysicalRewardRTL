// 3x2 unsigned multiplier (registered).
module mul3x2 (
    input  wire clk,
    input  wire rst_n,
    input  wire [2:0] a,
    input  wire [1:0] b,
    output reg  [4:0] product
);
    always @(posedge clk) begin
        if (!rst_n) product <= 5'd0;
        else        product <= a * b;
    end
endmodule
