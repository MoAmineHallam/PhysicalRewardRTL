// 13-bit two's complement negation (-in) (registered).
module neg_twos13b (
    input  wire clk, rst_n,
    input  wire [12:0] in,
    output reg  [12:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else        out <= (~in + 1'b1);
    end
endmodule
