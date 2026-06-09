// 11-bit unsigned saturating adder (registered).
module satadd11b (
    input  wire clk, rst_n,
    input  wire [10:0] a,
    input  wire [10:0] b,
    output reg  [10:0] sum
);
    wire [11:0] full = a + b;
    always @(posedge clk) begin
        if (!rst_n) sum <= 0;
        else        sum <= full[11] ? 11'd2047 : full[10:0];
    end
endmodule
