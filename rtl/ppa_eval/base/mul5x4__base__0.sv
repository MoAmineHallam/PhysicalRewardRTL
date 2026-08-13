module mul5x4__base__0 (
    input  wire clk,
    input  wire rst_n,
    input  wire [4:0] a,
    input  wire [3:0] b,
    output reg  [8:0] product
);

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        product <= 9'b0;
    end else begin
        product <= a * b;
    end
end

endmodule