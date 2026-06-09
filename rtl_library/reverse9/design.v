// 9-bit bit-reverse (registered).
module reverse9 (
    input  wire clk, rst_n,
    input  wire [8:0] in,
    output reg  [8:0] out
);
    integer k;
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else for (k=0;k<9;k=k+1) out[k] <= in[8-k];
    end
endmodule
