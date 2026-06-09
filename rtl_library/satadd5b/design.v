// 5-bit unsigned saturating adder (registered).
module satadd5b (
    input  wire clk, rst_n,
    input  wire [4:0] a,
    input  wire [4:0] b,
    output reg  [4:0] sum
);
    wire [5:0] full = a + b;
    always @(posedge clk) begin
        if (!rst_n) sum <= 0;
        else        sum <= full[5] ? 5'd31 : full[4:0];
    end
endmodule
