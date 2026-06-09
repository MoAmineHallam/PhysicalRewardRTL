// 8-bit half-swap: out = {lo, hi} (registered).
module halfswap8 (
    input  wire clk, rst_n,
    input  wire [7:0] in,
    output reg  [7:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else        out <= {in[3:0], in[7:4]};
    end
endmodule
