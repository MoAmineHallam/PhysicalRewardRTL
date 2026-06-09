// 12-bit one's complement (~in) (registered).
module neg_ones12b (
    input  wire clk, rst_n,
    input  wire [11:0] in,
    output reg  [11:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else        out <= ~in;
    end
endmodule
