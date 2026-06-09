// 16-bit min of two inputs (registered).
module min16b (
    input  wire clk, rst_n,
    input  wire [15:0] a,
    input  wire [15:0] b,
    output reg  [15:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else        out <= (a < b) ? a : b;
    end
endmodule
