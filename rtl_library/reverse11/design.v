// 11-bit bit-reverse (registered).
module reverse11 (
    input  wire clk, rst_n,
    input  wire [10:0] in,
    output reg  [10:0] out
);
    integer k;
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else for (k=0;k<11;k=k+1) out[k] <= in[10-k];
    end
endmodule
