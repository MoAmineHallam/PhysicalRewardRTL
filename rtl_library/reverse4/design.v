// 4-bit bit-reverse (registered).
module reverse4 (
    input  wire clk, rst_n,
    input  wire [3:0] in,
    output reg  [3:0] out
);
    integer k;
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else for (k=0;k<4;k=k+1) out[k] <= in[3-k];
    end
endmodule
