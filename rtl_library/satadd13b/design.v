// 13-bit unsigned saturating adder (registered).
module satadd13b (
    input  wire clk, rst_n,
    input  wire [12:0] a,
    input  wire [12:0] b,
    output reg  [12:0] sum
);
    wire [13:0] full = a + b;
    always @(posedge clk) begin
        if (!rst_n) sum <= 0;
        else        sum <= full[13] ? 13'd8191 : full[12:0];
    end
endmodule
