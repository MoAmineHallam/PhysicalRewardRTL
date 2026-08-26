module mlp_s1__poly8_v9_8b__g1 (
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
            // (the same function as the reference).
            // Horner's method matches the equation, no extra partial
            // products or additions needed.
            y <= (((((((((65 * x + 30) * x + 3) * x + 97) * x + 7) * x + 99) * x + 95) * x + 42) * x + 1)) & 16'hFFFF;
        end
    end
endmodule
