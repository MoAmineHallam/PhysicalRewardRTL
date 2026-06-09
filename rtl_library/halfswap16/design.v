// 16-bit half-swap: out = {lo, hi} (registered).
module halfswap16 (
    input  wire clk, rst_n,
    input  wire [15:0] in,
    output reg  [15:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else        out <= {in[7:0], in[15:8]};
    end
endmodule
