// 6x8 unsigned multiplier (registered).
module mul6x8 (
    input  wire clk,
    input  wire rst_n,
    input  wire [5:0] a,
    input  wire [7:0] b,
    output reg  [13:0] product
);
    always @(posedge clk) begin
        if (!rst_n) product <= 14'd0;
        else        product <= a * b;
    end
endmodule
