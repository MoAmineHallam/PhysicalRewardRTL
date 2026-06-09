// 6-bit rotate-left by 2 (registered).
module rotl6_2 (
    input  wire clk, rst_n,
    input  wire [5:0] in,
    output reg  [5:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else        out <= {in[3:0], in[5:4]};
    end
endmodule
