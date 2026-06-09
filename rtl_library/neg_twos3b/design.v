// 3-bit two's complement negation (-in) (registered).
module neg_twos3b (
    input  wire clk, rst_n,
    input  wire [2:0] in,
    output reg  [2:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else        out <= (~in + 1'b1);
    end
endmodule
