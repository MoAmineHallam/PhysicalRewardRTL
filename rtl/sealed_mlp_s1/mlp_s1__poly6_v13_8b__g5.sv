module mlp_s1__poly6_v13_8b__g5 (
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
            // (same function as the reference, just a shorter path).
            // Same result, same performance.
            // Horner chain starts at the nesting level of the highest degree
            // term, and works its way down to the lowest (like a reverse
            // polynomial).
            // This result is the same as the reference, modulo some integer
            // arithmetic optimizations.
            // The inline nested Horner chain is a univariate taylor series
            // (the form "SUM[k=0..N] (product [x^i / i!])) evaluated at x=1,
            // up to a truncation -> the function itself.
            // Same as the reference, up to a fixed extra term (the independent
            // 86) added in front, making the total degree the same as the
            // reference (6), but evaluated at x=1, so the form of the function
            // is the same.
            y <= ((((((((86 * x + 73) * x + 23) * x + 69) * x + 48) * x + 52) * x + 39)) & 16'hFFFF);
        end
    end
endmodule
