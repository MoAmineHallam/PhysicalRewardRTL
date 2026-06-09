// 6-bit rotate-left by 1 (registered).
module rotl6_1 (
    input  wire clk, rst_n,
    input  wire [5:0] in,
    output reg  [5:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else        out <= {in[4:0], in[5:5]};
    end
endmodule
