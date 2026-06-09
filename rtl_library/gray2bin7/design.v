// 7-bit Gray-to-binary decoder (registered).
module gray2bin7 (
    input  wire clk, rst_n,
    input  wire [6:0] gray,
    output reg  [6:0] bin
);
    always @(posedge clk) begin
        if (!rst_n) bin <= 0;
        else        bin <= (gray >> 0) ^ (gray >> 1) ^ (gray >> 2) ^ (gray >> 3) ^ (gray >> 4) ^ (gray >> 5) ^ (gray >> 6);
    end
endmodule
