// 9-bit unsigned saturating adder (registered).
module satadd9b (
    input  wire clk, rst_n,
    input  wire [8:0] a,
    input  wire [8:0] b,
    output reg  [8:0] sum
);
    wire [9:0] full = a + b;
    always @(posedge clk) begin
        if (!rst_n) sum <= 0;
        else        sum <= full[9] ? 9'd511 : full[8:0];
    end
endmodule
