// 14-bit two's complement negation (-in) (registered).
module neg_twos14b (
    input  wire clk, rst_n,
    input  wire [13:0] in,
    output reg  [13:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else        out <= (~in + 1'b1);
    end
endmodule
