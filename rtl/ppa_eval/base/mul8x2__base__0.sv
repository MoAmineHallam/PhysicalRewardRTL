module mul8x2__base__0 (
    input  wire clk,
    input  wire rst_n,
    input  wire [7:0] a,
    input  wire [1:0] b,
    output reg  [9:0] product
);

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        product <= 10'd0;
    end else begin
        product <= a * b;
    end
end

endmodule