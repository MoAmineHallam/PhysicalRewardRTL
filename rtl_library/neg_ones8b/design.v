// 8-bit one's complement (~in) (registered).
module neg_ones8b (
    input  wire clk, rst_n,
    input  wire [7:0] in,
    output reg  [7:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else        out <= ~in;
    end
endmodule
