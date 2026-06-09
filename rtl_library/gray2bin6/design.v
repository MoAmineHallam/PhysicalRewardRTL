// 6-bit Gray-to-binary decoder (registered).
module gray2bin6 (
    input  wire clk, rst_n,
    input  wire [5:0] gray,
    output reg  [5:0] bin
);
    always @(posedge clk) begin
        if (!rst_n) bin <= 0;
        else        bin <= (gray >> 0) ^ (gray >> 1) ^ (gray >> 2) ^ (gray >> 3) ^ (gray >> 4) ^ (gray >> 5);
    end
endmodule
