// 10-bit rotate-left by 5 (registered).
module rotl10_5 (
    input  wire clk, rst_n,
    input  wire [9:0] in,
    output reg  [9:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else        out <= {in[4:0], in[9:5]};
    end
endmodule
