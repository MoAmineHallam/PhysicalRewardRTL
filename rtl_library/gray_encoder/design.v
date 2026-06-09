// Registered binary-to-Gray code converter (4-bit).
module gray_encoder (
    input  wire       clk,
    input  wire       rst_n,
    input  wire [3:0] bin,
    output reg  [3:0] gray
);
    always @(posedge clk) begin
        if (!rst_n) gray <= 4'b0;
        else        gray <= bin ^ (bin >> 1);
    end
endmodule
