// signed 2x2 multiplier (registered).
module smul2x2 (
    input  wire clk, rst_n,
    input  wire signed [1:0] a,
    input  wire signed [1:0] b,
    output reg  signed [3:0] product
);
    always @(posedge clk) begin
        if (!rst_n) product <= 0;
        else        product <= a * b;
    end
endmodule
