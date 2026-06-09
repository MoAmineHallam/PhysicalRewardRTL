// 7-bit one's complement (~in) (registered).
module neg_ones7b (
    input  wire clk, rst_n,
    input  wire [6:0] in,
    output reg  [6:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else        out <= ~in;
    end
endmodule
