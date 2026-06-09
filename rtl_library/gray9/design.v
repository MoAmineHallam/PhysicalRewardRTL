// 9-bit binary->Gray (registered).
module gray9 (
    input  wire clk, rst_n,
    input  wire [8:0] bin,
    output reg  [8:0] gray
);
    always @(posedge clk) begin
        if (!rst_n) gray <= 0;
        else        gray <= bin ^ (bin >> 1);
    end
endmodule
