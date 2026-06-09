// 12-bit MAC: acc <= acc + a*b (6-bit operands).
module mac6_12b (
    input  wire clk, rst_n,
    input  wire [5:0] a,
    input  wire [5:0] b,
    output reg  [11:0] acc
);
    always @(posedge clk) begin
        if (!rst_n) acc <= 0;
        else        acc <= acc + a * b;
    end
endmodule
