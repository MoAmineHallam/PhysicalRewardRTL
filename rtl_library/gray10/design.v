// 10-bit binary->Gray (registered).
module gray10 (
    input  wire clk, rst_n,
    input  wire [9:0] bin,
    output reg  [9:0] gray
);
    always @(posedge clk) begin
        if (!rst_n) gray <= 0;
        else        gray <= bin ^ (bin >> 1);
    end
endmodule
