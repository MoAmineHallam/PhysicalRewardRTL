// 9-bit max of two inputs (registered).
module max9b (
    input  wire clk, rst_n,
    input  wire [8:0] a,
    input  wire [8:0] b,
    output reg  [8:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else        out <= (a > b) ? a : b;
    end
endmodule
