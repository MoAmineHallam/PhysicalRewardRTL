// 8-bit bit-reverse (registered).
module reverse8 (
    input  wire clk, rst_n,
    input  wire [7:0] in,
    output reg  [7:0] out
);
    integer k;
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else for (k=0;k<8;k=k+1) out[k] <= in[7-k];
    end
endmodule
