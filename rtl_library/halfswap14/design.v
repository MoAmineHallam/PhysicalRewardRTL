// 14-bit half-swap: out = {lo, hi} (registered).
module halfswap14 (
    input  wire clk, rst_n,
    input  wire [13:0] in,
    output reg  [13:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else        out <= {in[6:0], in[13:7]};
    end
endmodule
