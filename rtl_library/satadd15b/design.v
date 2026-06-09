// 15-bit unsigned saturating adder (registered).
module satadd15b (
    input  wire clk, rst_n,
    input  wire [14:0] a,
    input  wire [14:0] b,
    output reg  [14:0] sum
);
    wire [15:0] full = a + b;
    always @(posedge clk) begin
        if (!rst_n) sum <= 0;
        else        sum <= full[15] ? 15'd32767 : full[14:0];
    end
endmodule
