// 9-bit two's complement absolute value (registered).
module abs9b (
    input  wire clk, rst_n,
    input  wire [8:0] in,
    output reg  [8:0] out
);
    always @(posedge clk) begin
        if (!rst_n)     out <= 0;
        else if (in[8]) out <= (~in + 1'b1);
        else            out <= in;
    end
endmodule
