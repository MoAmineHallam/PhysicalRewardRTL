// 12-bit min of two inputs (registered).
module min12b (
    input  wire clk, rst_n,
    input  wire [11:0] a,
    input  wire [11:0] b,
    output reg  [11:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else        out <= (a < b) ? a : b;
    end
endmodule
