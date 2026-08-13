module mul8x2__base__6 (
    input  wire clk,
    input  wire rst_n,
    input  wire [7:0] a,
    input  wire [1:0] b,
    output reg  [9:0] product
);

always @(posedge clk) begin
    if (!rst_n) begin
        product <= 0;
    end else begin
        product <= a * b;
    end
end

endmodule