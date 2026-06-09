// 8-bit unsigned saturating adder (registered).
module satadd8b (
    input  wire clk, rst_n,
    input  wire [7:0] a,
    input  wire [7:0] b,
    output reg  [7:0] sum
);
    wire [8:0] full = a + b;
    always @(posedge clk) begin
        if (!rst_n) sum <= 0;
        else        sum <= full[8] ? 8'd255 : full[7:0];
    end
endmodule
