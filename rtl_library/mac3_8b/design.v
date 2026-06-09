// 8-bit MAC: acc <= acc + a*b (3-bit operands).
module mac3_8b (
    input  wire clk, rst_n,
    input  wire [2:0] a,
    input  wire [2:0] b,
    output reg  [7:0] acc
);
    always @(posedge clk) begin
        if (!rst_n) acc <= 0;
        else        acc <= acc + a * b;
    end
endmodule
