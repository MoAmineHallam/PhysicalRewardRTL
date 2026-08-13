module mul5x5__base__6 (
    input  wire clk,
    input  wire rst_n,
    input  wire [4:0] a,
    input  wire [4:0] b,
    output reg  [9:0] product
);

always @(posedge clk)
    if (!rst_n)
        product <= 0;
    else
        product <= a * b;

endmodule