// 7x7 unsigned multiplier (registered).
module mul7x7 (
    input  wire clk,
    input  wire rst_n,
    input  wire [6:0] a,
    input  wire [6:0] b,
    output reg  [13:0] product
);
    always @(posedge clk) begin
        if (!rst_n) product <= 14'd0;
        else        product <= a * b;
    end
endmodule
