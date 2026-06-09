// 16-bit rotate-left by 4 (registered).
module rotl16_4 (
    input  wire clk, rst_n,
    input  wire [15:0] in,
    output reg  [15:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else        out <= {in[11:0], in[15:12]};
    end
endmodule
