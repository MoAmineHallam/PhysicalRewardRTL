// signed 4x4 multiplier (registered).
module smul4x4 (
    input  wire clk, rst_n,
    input  wire signed [3:0] a,
    input  wire signed [3:0] b,
    output reg  signed [7:0] product
);
    always @(posedge clk) begin
        if (!rst_n) product <= 0;
        else        product <= a * b;
    end
endmodule
