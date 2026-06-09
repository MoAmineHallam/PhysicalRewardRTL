// 7-bit bit-reverse (registered).
module reverse7 (
    input  wire clk, rst_n,
    input  wire [6:0] in,
    output reg  [6:0] out
);
    integer k;
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else for (k=0;k<7;k=k+1) out[k] <= in[6-k];
    end
endmodule
