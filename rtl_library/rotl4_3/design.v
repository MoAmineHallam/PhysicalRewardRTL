// 4-bit rotate-left by 3 (registered).
module rotl4_3 (
    input  wire clk, rst_n,
    input  wire [3:0] in,
    output reg  [3:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else        out <= {in[0:0], in[3:1]};
    end
endmodule
