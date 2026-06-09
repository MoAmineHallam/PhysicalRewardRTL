// 10-bit rotate-left by 2 (registered).
module rotl10_2 (
    input  wire clk, rst_n,
    input  wire [9:0] in,
    output reg  [9:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else        out <= {in[7:0], in[9:8]};
    end
endmodule
