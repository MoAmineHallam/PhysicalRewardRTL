// 16-bit Gray-to-binary decoder (registered).
module gray2bin16 (
    input  wire clk, rst_n,
    input  wire [15:0] gray,
    output reg  [15:0] bin
);
    always @(posedge clk) begin
        if (!rst_n) bin <= 0;
        else        bin <= (gray >> 0) ^ (gray >> 1) ^ (gray >> 2) ^ (gray >> 3) ^ (gray >> 4) ^ (gray >> 5) ^ (gray >> 6) ^ (gray >> 7) ^ (gray >> 8) ^ (gray >> 9) ^ (gray >> 10) ^ (gray >> 11) ^ (gray >> 12) ^ (gray >> 13) ^ (gray >> 14) ^ (gray >> 15);
    end
endmodule
