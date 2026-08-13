module mul8x3__base__5 (
    input  wire clk,
    input  wire rst_n,
    input  wire [7:0] a,
    input  wire [2:0] b,
    output reg  [10:0] product
);

always @(posedge clk) begin
    if (!rst_n) begin
        product <= 0;
    end else begin
        product <= a * b;
    end
end

endmodule