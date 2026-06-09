// 12-bit rotate-left by 1 (registered).
module rotl12_1 (
    input  wire clk, rst_n,
    input  wire [11:0] in,
    output reg  [11:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else        out <= {in[10:0], in[11:11]};
    end
endmodule
