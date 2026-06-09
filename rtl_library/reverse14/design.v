// 14-bit bit-reverse (registered).
module reverse14 (
    input  wire clk, rst_n,
    input  wire [13:0] in,
    output reg  [13:0] out
);
    integer k;
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else for (k=0;k<14;k=k+1) out[k] <= in[13-k];
    end
endmodule
