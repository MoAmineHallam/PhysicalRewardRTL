module mul7x2__base__6 (
    input  wire clk,
    input  wire rst_n,
    input  wire [6:0] a,
    input  wire [1:0] b,
    output reg  [8:0] product
);

always @(posedge clk) begin
    if (!rst_n) begin
        product <= 9'b0;
    end else begin
        product <= a * b;
    end
end

endmodule