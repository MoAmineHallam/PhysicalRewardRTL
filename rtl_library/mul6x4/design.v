// 6x4 unsigned multiplier (registered).
module mul6x4 (
    input  wire clk,
    input  wire rst_n,
    input  wire [5:0] a,
    input  wire [3:0] b,
    output reg  [9:0] product
);
    always @(posedge clk) begin
        if (!rst_n) product <= 10'd0;
        else        product <= a * b;
    end
endmodule
