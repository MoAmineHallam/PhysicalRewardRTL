module mul3x7__base__2 (
    input  wire clk,
    input  wire rst_n,
    input  wire [2:0] a,
    input  wire [6:0] b,
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