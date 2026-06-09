// 16-bit bit-reverse (registered).
module reverse16 (
    input  wire clk, rst_n,
    input  wire [15:0] in,
    output reg  [15:0] out
);
    integer k;
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else for (k=0;k<16;k=k+1) out[k] <= in[15-k];
    end
endmodule
