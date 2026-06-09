// 8-bit rotate-left by 1 (registered).
module rotl8_1 (
    input  wire clk, rst_n,
    input  wire [7:0] in,
    output reg  [7:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else        out <= {in[6:0], in[7:7]};
    end
endmodule
