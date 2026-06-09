// 6x2 unsigned multiplier (registered).
module mul6x2 (
    input  wire clk,
    input  wire rst_n,
    input  wire [5:0] a,
    input  wire [1:0] b,
    output reg  [7:0] product
);
    always @(posedge clk) begin
        if (!rst_n) product <= 8'd0;
        else        product <= a * b;
    end
endmodule
