// 3-bit unsigned saturating adder (registered).
module satadd3b (
    input  wire clk, rst_n,
    input  wire [2:0] a,
    input  wire [2:0] b,
    output reg  [2:0] sum
);
    wire [3:0] full = a + b;
    always @(posedge clk) begin
        if (!rst_n) sum <= 0;
        else        sum <= full[3] ? 3'd7 : full[2:0];
    end
endmodule
