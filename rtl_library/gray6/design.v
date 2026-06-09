// 6-bit binary->Gray (registered).
module gray6 (
    input  wire clk, rst_n,
    input  wire [5:0] bin,
    output reg  [5:0] gray
);
    always @(posedge clk) begin
        if (!rst_n) gray <= 0;
        else        gray <= bin ^ (bin >> 1);
    end
endmodule
