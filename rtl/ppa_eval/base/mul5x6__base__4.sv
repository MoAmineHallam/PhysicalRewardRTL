module mul5x6__base__4 (
    input  wire clk,
    input  wire rst_n,
    input  wire [4:0] a,
    input  wire [5:0] b,
    output reg  [10:0] product
);

always @(posedge clk or negedge rst_n) begin
    if (~rst_n) begin
        product <= 11'b0;
    end else begin
        product <= a * b;
    end
end

endmodule