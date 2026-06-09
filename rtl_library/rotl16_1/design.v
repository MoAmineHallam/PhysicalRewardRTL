// 16-bit rotate-left by 1 (registered).
module rotl16_1 (
    input  wire clk, rst_n,
    input  wire [15:0] in,
    output reg  [15:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else        out <= {in[14:0], in[15:15]};
    end
endmodule
