// 14-bit unsigned saturating adder (registered).
module satadd14b (
    input  wire clk, rst_n,
    input  wire [13:0] a,
    input  wire [13:0] b,
    output reg  [13:0] sum
);
    wire [14:0] full = a + b;
    always @(posedge clk) begin
        if (!rst_n) sum <= 0;
        else        sum <= full[14] ? 14'd16383 : full[13:0];
    end
endmodule
