module mul7x3__base__6 (
    input  wire clk,
    input  wire rst_n,
    input  wire [6:0] a,
    input  wire [2:0] b,
    output reg  [9:0] product
);

always @(posedge clk) begin
    if (!rst_n) begin
        product <= 10'd0;
    end else begin
        product <= a * b;
    end
end

endmodule