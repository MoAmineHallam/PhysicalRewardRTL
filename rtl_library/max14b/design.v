// 14-bit max of two inputs (registered).
module max14b (
    input  wire clk, rst_n,
    input  wire [13:0] a,
    input  wire [13:0] b,
    output reg  [13:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else        out <= (a > b) ? a : b;
    end
endmodule
