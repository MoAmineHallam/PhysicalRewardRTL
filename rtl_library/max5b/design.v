// 5-bit max of two inputs (registered).
module max5b (
    input  wire clk, rst_n,
    input  wire [4:0] a,
    input  wire [4:0] b,
    output reg  [4:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else        out <= (a > b) ? a : b;
    end
endmodule
