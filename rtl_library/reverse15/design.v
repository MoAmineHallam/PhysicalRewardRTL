// 15-bit bit-reverse (registered).
module reverse15 (
    input  wire clk, rst_n,
    input  wire [14:0] in,
    output reg  [14:0] out
);
    integer k;
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else for (k=0;k<15;k=k+1) out[k] <= in[14-k];
    end
endmodule
