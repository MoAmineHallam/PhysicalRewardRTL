// 8-bit MAC: acc <= acc + a*b (2-bit operands).
module mac2_8b (
    input  wire clk, rst_n,
    input  wire [1:0] a,
    input  wire [1:0] b,
    output reg  [7:0] acc
);
    always @(posedge clk) begin
        if (!rst_n) acc <= 0;
        else        acc <= acc + a * b;
    end
endmodule
