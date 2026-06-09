// 12-bit rotate-left by 6 (registered).
module rotl12_6 (
    input  wire clk, rst_n,
    input  wire [11:0] in,
    output reg  [11:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else        out <= {in[5:0], in[11:6]};
    end
endmodule
