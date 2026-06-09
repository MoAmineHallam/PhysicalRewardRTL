// 3-bit two's complement absolute value (registered).
module abs3b (
    input  wire clk, rst_n,
    input  wire [2:0] in,
    output reg  [2:0] out
);
    always @(posedge clk) begin
        if (!rst_n)     out <= 0;
        else if (in[2]) out <= (~in + 1'b1);
        else            out <= in;
    end
endmodule
