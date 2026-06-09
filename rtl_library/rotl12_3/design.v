// 12-bit rotate-left by 3 (registered).
module rotl12_3 (
    input  wire clk, rst_n,
    input  wire [11:0] in,
    output reg  [11:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else        out <= {in[8:0], in[11:9]};
    end
endmodule
