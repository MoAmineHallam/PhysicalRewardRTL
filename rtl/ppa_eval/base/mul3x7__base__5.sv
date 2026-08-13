module mul3x7__base__5 (
    input  wire clk,
    input  wire rst_n,
    input  wire [2:0] a,
    input  wire [6:0] b,
    output reg  [9:0] product
);

always @(posedge clk, negedge rst_n) begin
    if (!rst_n) begin
        product <= 0;
    end else begin
        product <= a * b;
    end
end

endmodule