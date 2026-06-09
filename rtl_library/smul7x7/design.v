// signed 7x7 multiplier (registered).
module smul7x7 (
    input  wire clk, rst_n,
    input  wire signed [6:0] a,
    input  wire signed [6:0] b,
    output reg  signed [13:0] product
);
    always @(posedge clk) begin
        if (!rst_n) product <= 0;
        else        product <= a * b;
    end
endmodule
