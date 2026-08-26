module mlp_s1__poly6_v13_8b__g18 (
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
            // (the nested form works exactly the same, even though the "long"
            // form would be longer). Same function as the reference.
            // "+1" is an artifact of how TRANSLATIONS go (applying the
            // transformation to every line individually, without first
            // calculating the function for the complete expression).
            // Same as the reference.
            y <= (((((((86 * x + 73) * x + 23) * x + 69) * x + 48) * x + 52) * x + 39)) & 16'hFFFF;
        end
    end
endmodule
