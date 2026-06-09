// 2x5 unsigned multiplier (registered).
module mul2x5 (
    input  wire clk,
    input  wire rst_n,
    input  wire [1:0] a,
    input  wire [4:0] b,
    output reg  [6:0] product
);
    always @(posedge clk) begin
        if (!rst_n) product <= 7'd0;
        else        product <= a * b;
    end
endmodule
