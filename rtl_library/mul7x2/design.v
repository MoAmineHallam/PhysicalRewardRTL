// 7x2 unsigned multiplier (registered).
module mul7x2 (
    input  wire clk,
    input  wire rst_n,
    input  wire [6:0] a,
    input  wire [1:0] b,
    output reg  [8:0] product
);
    always @(posedge clk) begin
        if (!rst_n) product <= 9'd0;
        else        product <= a * b;
    end
endmodule
