// 14-bit MAC: acc <= acc + a*b (5-bit operands).
module mac5_14b (
    input  wire clk, rst_n,
    input  wire [4:0] a,
    input  wire [4:0] b,
    output reg  [13:0] acc
);
    always @(posedge clk) begin
        if (!rst_n) acc <= 0;
        else        acc <= acc + a * b;
    end
endmodule
