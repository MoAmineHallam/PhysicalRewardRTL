module mlp_s1__poly16_v13_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    always @(posedge clk) begin
        if (!rst_n) begin
            y <= 16'd0;
        end else begin
            // Degree-16 Horner polynomial, mod 2^16
            // (the long form of the polynomial, without the inner
            // parentheses, explicitly nested the multiplication and
            // the addition).
            // Equivalent to the reference, confirming that the long
            // form is exactly the same as the Horner form.
            y <= ((((((((((((((((45 * x + 67) * x + 56) * x + 54) * x + 26) * x + 74) * x + 47) * x + 10) * x + 96) * x + 73) * x + 22) * x + 53) * x + 23) * x + 53) * x + 77) * x + 32) * x + 61);
        end
    end
endmodule
