// 5-bit bit-reverse (registered).
module reverse5 (
    input  wire clk, rst_n,
    input  wire [4:0] in,
    output reg  [4:0] out
);
    integer k;
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else for (k=0;k<5;k=k+1) out[k] <= in[4-k];
    end
endmodule
