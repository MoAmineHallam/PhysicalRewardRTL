// 5-bit Gray-to-binary decoder (registered).
module gray2bin5 (
    input  wire clk, rst_n,
    input  wire [4:0] gray,
    output reg  [4:0] bin
);
    always @(posedge clk) begin
        if (!rst_n) bin <= 0;
        else        bin <= (gray >> 0) ^ (gray >> 1) ^ (gray >> 2) ^ (gray >> 3) ^ (gray >> 4);
    end
endmodule
