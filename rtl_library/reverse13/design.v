// 13-bit bit-reverse (registered).
module reverse13 (
    input  wire clk, rst_n,
    input  wire [12:0] in,
    output reg  [12:0] out
);
    integer k;
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else for (k=0;k<13;k=k+1) out[k] <= in[12-k];
    end
endmodule
