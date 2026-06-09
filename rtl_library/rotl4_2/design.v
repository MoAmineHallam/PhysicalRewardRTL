// 4-bit rotate-left by 2 (registered).
module rotl4_2 (
    input  wire clk, rst_n,
    input  wire [3:0] in,
    output reg  [3:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else        out <= {in[1:0], in[3:2]};
    end
endmodule
