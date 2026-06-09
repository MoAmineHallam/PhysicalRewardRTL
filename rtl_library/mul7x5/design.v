// 7x5 unsigned multiplier (registered).
module mul7x5 (
    input  wire clk,
    input  wire rst_n,
    input  wire [6:0] a,
    input  wire [4:0] b,
    output reg  [11:0] product
);
    always @(posedge clk) begin
        if (!rst_n) product <= 12'd0;
        else        product <= a * b;
    end
endmodule
