// 13-bit binary->Gray (registered).
module gray13 (
    input  wire clk, rst_n,
    input  wire [12:0] bin,
    output reg  [12:0] gray
);
    always @(posedge clk) begin
        if (!rst_n) gray <= 0;
        else        gray <= bin ^ (bin >> 1);
    end
endmodule
