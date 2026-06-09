// 7-bit unsigned saturating adder (registered).
module satadd7b (
    input  wire clk, rst_n,
    input  wire [6:0] a,
    input  wire [6:0] b,
    output reg  [6:0] sum
);
    wire [7:0] full = a + b;
    always @(posedge clk) begin
        if (!rst_n) sum <= 0;
        else        sum <= full[7] ? 7'd127 : full[6:0];
    end
endmodule
