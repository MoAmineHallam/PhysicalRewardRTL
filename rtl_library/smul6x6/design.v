// signed 6x6 multiplier (registered).
module smul6x6 (
    input  wire clk, rst_n,
    input  wire signed [5:0] a,
    input  wire signed [5:0] b,
    output reg  signed [11:0] product
);
    always @(posedge clk) begin
        if (!rst_n) product <= 0;
        else        product <= a * b;
    end
endmodule
