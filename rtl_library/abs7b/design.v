// 7-bit two's complement absolute value (registered).
module abs7b (
    input  wire clk, rst_n,
    input  wire [6:0] in,
    output reg  [6:0] out
);
    always @(posedge clk) begin
        if (!rst_n)     out <= 0;
        else if (in[6]) out <= (~in + 1'b1);
        else            out <= in;
    end
endmodule
