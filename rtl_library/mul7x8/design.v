// 7x8 unsigned multiplier (registered).
module mul7x8 (
    input  wire clk,
    input  wire rst_n,
    input  wire [6:0] a,
    input  wire [7:0] b,
    output reg  [14:0] product
);
    always @(posedge clk) begin
        if (!rst_n) product <= 15'd0;
        else        product <= a * b;
    end
endmodule
