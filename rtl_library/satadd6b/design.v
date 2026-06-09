// 6-bit unsigned saturating adder (registered).
module satadd6b (
    input  wire clk, rst_n,
    input  wire [5:0] a,
    input  wire [5:0] b,
    output reg  [5:0] sum
);
    wire [6:0] full = a + b;
    always @(posedge clk) begin
        if (!rst_n) sum <= 0;
        else        sum <= full[6] ? 6'd63 : full[5:0];
    end
endmodule
