// Registered absolute value of 4-bit two's complement input.
module abs_val (
    input  wire       clk,
    input  wire       rst_n,
    input  wire [3:0] in,
    output reg  [3:0] out
);
    always @(posedge clk) begin
        if (!rst_n)    out <= 4'b0;
        else if (in[3]) out <= (~in + 4'd1);
        else            out <= in;
    end
endmodule
