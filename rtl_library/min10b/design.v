// 10-bit min of two inputs (registered).
module min10b (
    input  wire clk, rst_n,
    input  wire [9:0] a,
    input  wire [9:0] b,
    output reg  [9:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else        out <= (a < b) ? a : b;
    end
endmodule
