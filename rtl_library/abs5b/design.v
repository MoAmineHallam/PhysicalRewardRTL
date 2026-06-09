// 5-bit two's complement absolute value (registered).
module abs5b (
    input  wire clk, rst_n,
    input  wire [4:0] in,
    output reg  [4:0] out
);
    always @(posedge clk) begin
        if (!rst_n)     out <= 0;
        else if (in[4]) out <= (~in + 1'b1);
        else            out <= in;
    end
endmodule
