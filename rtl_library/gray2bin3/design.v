// 3-bit Gray-to-binary decoder (registered).
module gray2bin3 (
    input  wire clk, rst_n,
    input  wire [2:0] gray,
    output reg  [2:0] bin
);
    always @(posedge clk) begin
        if (!rst_n) bin <= 0;
        else        bin <= (gray >> 0) ^ (gray >> 1) ^ (gray >> 2);
    end
endmodule
