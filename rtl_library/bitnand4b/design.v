// 4-bit bitwise NAND of two inputs (registered).
module bitnand4b (
    input  wire clk, rst_n,
    input  wire [3:0] a,
    input  wire [3:0] b,
    output reg  [3:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else        out <= ~(a & b);
    end
endmodule
