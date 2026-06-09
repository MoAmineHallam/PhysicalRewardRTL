// 4x8 unsigned multiplier (registered).
module mul4x8 (
    input  wire clk,
    input  wire rst_n,
    input  wire [3:0] a,
    input  wire [7:0] b,
    output reg  [11:0] product
);
    always @(posedge clk) begin
        if (!rst_n) product <= 12'd0;
        else        product <= a * b;
    end
endmodule
