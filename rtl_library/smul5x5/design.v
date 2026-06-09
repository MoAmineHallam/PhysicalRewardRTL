// signed 5x5 multiplier (registered).
module smul5x5 (
    input  wire clk, rst_n,
    input  wire signed [4:0] a,
    input  wire signed [4:0] b,
    output reg  signed [9:0] product
);
    always @(posedge clk) begin
        if (!rst_n) product <= 0;
        else        product <= a * b;
    end
endmodule
