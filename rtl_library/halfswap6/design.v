// 6-bit half-swap: out = {lo, hi} (registered).
module halfswap6 (
    input  wire clk, rst_n,
    input  wire [5:0] in,
    output reg  [5:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else        out <= {in[2:0], in[5:3]};
    end
endmodule
