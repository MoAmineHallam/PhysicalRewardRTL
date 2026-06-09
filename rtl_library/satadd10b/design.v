// 10-bit unsigned saturating adder (registered).
module satadd10b (
    input  wire clk, rst_n,
    input  wire [9:0] a,
    input  wire [9:0] b,
    output reg  [9:0] sum
);
    wire [10:0] full = a + b;
    always @(posedge clk) begin
        if (!rst_n) sum <= 0;
        else        sum <= full[10] ? 10'd1023 : full[9:0];
    end
endmodule
