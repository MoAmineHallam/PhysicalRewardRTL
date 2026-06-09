// 3x6 unsigned multiplier (registered).
module mul3x6 (
    input  wire clk,
    input  wire rst_n,
    input  wire [2:0] a,
    input  wire [5:0] b,
    output reg  [8:0] product
);
    always @(posedge clk) begin
        if (!rst_n) product <= 9'd0;
        else        product <= a * b;
    end
endmodule
