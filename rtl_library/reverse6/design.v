// 6-bit bit-reverse (registered).
module reverse6 (
    input  wire clk, rst_n,
    input  wire [5:0] in,
    output reg  [5:0] out
);
    integer k;
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else for (k=0;k<6;k=k+1) out[k] <= in[5-k];
    end
endmodule
