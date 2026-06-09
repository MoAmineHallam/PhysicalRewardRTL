// 15-bit binary->Gray (registered).
module gray15 (
    input  wire clk, rst_n,
    input  wire [14:0] bin,
    output reg  [14:0] gray
);
    always @(posedge clk) begin
        if (!rst_n) gray <= 0;
        else        gray <= bin ^ (bin >> 1);
    end
endmodule
