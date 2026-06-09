// 12-bit bit-reverse (registered).
module reverse12 (
    input  wire clk, rst_n,
    input  wire [11:0] in,
    output reg  [11:0] out
);
    integer k;
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else for (k=0;k<12;k=k+1) out[k] <= in[11-k];
    end
endmodule
