module mul2x8__base__4 (
    input  wire clk,
    input  wire rst_n,
    input  wire [1:0] a,
    input  wire [7:0] b,
    output reg  [9:0] product
);

always @(posedge clk) begin
    if (!rst_n) begin
        product <= 10'b0;
    end else begin
        product <= a * b;
    end
end

endmodule