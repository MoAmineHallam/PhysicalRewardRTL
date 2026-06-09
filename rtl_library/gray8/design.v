// 8-bit binary->Gray (registered).
module gray8 (
    input  wire clk, rst_n,
    input  wire [7:0] bin,
    output reg  [7:0] gray
);
    always @(posedge clk) begin
        if (!rst_n) gray <= 0;
        else        gray <= bin ^ (bin >> 1);
    end
endmodule
