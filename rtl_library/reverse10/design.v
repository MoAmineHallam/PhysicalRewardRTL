// 10-bit bit-reverse (registered).
module reverse10 (
    input  wire clk, rst_n,
    input  wire [9:0] in,
    output reg  [9:0] out
);
    integer k;
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else for (k=0;k<10;k=k+1) out[k] <= in[9-k];
    end
endmodule
