module mul5x4__base__3 (
    input  wire clk,
    input  wire rst_n,
    input  wire [4:0] a,
    input  wire [3:0] b,
    output reg  [8:0] product
);

always @(posedge clk) begin
    if (rst_n == 1'b0) begin
        product <= 9'b0;
    end else begin
        product <= a * b;
    end
end

endmodule