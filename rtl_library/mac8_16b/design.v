// 16-bit MAC: acc <= acc + a*b (8-bit operands).
module mac8_16b (
    input  wire clk, rst_n,
    input  wire [7:0] a,
    input  wire [7:0] b,
    output reg  [15:0] acc
);
    always @(posedge clk) begin
        if (!rst_n) acc <= 0;
        else        acc <= acc + a * b;
    end
endmodule
