// 8-bit rotate-left by 2 (registered).
module rotl8_2 (
    input  wire clk, rst_n,
    input  wire [7:0] in,
    output reg  [7:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else        out <= {in[5:0], in[7:6]};
    end
endmodule
