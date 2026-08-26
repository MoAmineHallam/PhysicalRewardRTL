module mlp_s1__poly8_v9_8b__g12 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    always @(posedge clk) begin
        if (!rst_n) begin
            y <= 16'd0;
        end else begin
            // Degree-8 Horner polynomial, mod 2^16
            // (the long form of the polynomial, essentially inline nested
            // Horner expressions, is the same as the reference).
            // See https://en.wikipedia.org/wiki/Horner_scheme
            // (FULL POLY, not the expanded one with omitted terms).
            // The mod 2^16 part is implicitly applied everywhere (regardless
            // of the polynomial).
            y <= (((((((((65 * x + 30) * x + 3) * x + 97) * x + 7) * x + 99) * x + 95) * x + 42) * x + 1)) & 16'hFFFF;
        end
    end
endmodule
