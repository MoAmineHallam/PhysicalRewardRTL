module mul5x7__base__1 (
    input  wire clk,
    input  wire rst_n,
    input  wire [4:0] a,
    input  wire [6:0] b,
    output reg  [11:0] product
);

always @(posedge clk)
begin
    if (!rst_n)
        product <= 12'b0;
    else
        product <= a * b;
end

endmodule