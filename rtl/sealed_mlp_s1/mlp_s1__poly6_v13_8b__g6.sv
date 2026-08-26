module mlp_s1__poly6_v13_8b__g6 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    always @(posedge clk) begin
        if (!rst_n) begin
            y <= 16'd0;
        end else begin
            // Degree-6 Horner polynomial, mod 2^16
            // TRANSPOSING THE MATRIX (same as the reference)
            // Equivalent to the nested Horner:
            // y = F0(F1(F2(F3(F4(F5(F6(x)))))))
            // As a single, inline, nested Horner expression.
            y <= (((((((86 * x + 73) * x + 23) * x + 69) * x + 48) * x + 52) * x + 39));
        end
    end
endmodule
