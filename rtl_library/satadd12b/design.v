// 12-bit unsigned saturating adder (registered).
module satadd12b (
    input  wire clk, rst_n,
    input  wire [11:0] a,
    input  wire [11:0] b,
    output reg  [11:0] sum
);
    wire [12:0] full = a + b;
    always @(posedge clk) begin
        if (!rst_n) sum <= 0;
        else        sum <= full[12] ? 12'd4095 : full[11:0];
    end
endmodule
