// 8-bit rotate-left by 4 (registered).
module rotl8_4 (
    input  wire clk, rst_n,
    input  wire [7:0] in,
    output reg  [7:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else        out <= {in[3:0], in[7:4]};
    end
endmodule
