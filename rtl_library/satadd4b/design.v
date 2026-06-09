// 4-bit unsigned saturating adder (registered).
module satadd4b (
    input  wire clk, rst_n,
    input  wire [3:0] a,
    input  wire [3:0] b,
    output reg  [3:0] sum
);
    wire [4:0] full = a + b;
    always @(posedge clk) begin
        if (!rst_n) sum <= 0;
        else        sum <= full[4] ? 4'd15 : full[3:0];
    end
endmodule
