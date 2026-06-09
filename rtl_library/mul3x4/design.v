// 3x4 unsigned multiplier (registered).
module mul3x4 (
    input  wire clk,
    input  wire rst_n,
    input  wire [2:0] a,
    input  wire [3:0] b,
    output reg  [6:0] product
);
    always @(posedge clk) begin
        if (!rst_n) product <= 7'd0;
        else        product <= a * b;
    end
endmodule
