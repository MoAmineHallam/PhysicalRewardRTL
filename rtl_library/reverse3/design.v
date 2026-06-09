// 3-bit bit-reverse (registered).
module reverse3 (
    input  wire clk, rst_n,
    input  wire [2:0] in,
    output reg  [2:0] out
);
    integer k;
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else for (k=0;k<3;k=k+1) out[k] <= in[2-k];
    end
endmodule
