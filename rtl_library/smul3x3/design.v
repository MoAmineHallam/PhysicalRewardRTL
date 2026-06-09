// signed 3x3 multiplier (registered).
module smul3x3 (
    input  wire clk, rst_n,
    input  wire signed [2:0] a,
    input  wire signed [2:0] b,
    output reg  signed [5:0] product
);
    always @(posedge clk) begin
        if (!rst_n) product <= 0;
        else        product <= a * b;
    end
endmodule
