// 4-bit rotate-left by 1 (registered).
module rotl4_1 (
    input  wire clk, rst_n,
    input  wire [3:0] in,
    output reg  [3:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else        out <= {in[2:0], in[3:3]};
    end
endmodule
