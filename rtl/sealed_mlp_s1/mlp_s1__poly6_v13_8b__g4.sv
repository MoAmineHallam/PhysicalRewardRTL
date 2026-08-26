module mlp_s1__poly6_v13_8b__g4 (
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
            // (the long form was manually expanded, so this is the same).
            // Same function as the reference.
            // The long form (explicit products and additions) is faster to
            // synthesize, so we use that.
            // The inline nested form is shorter, but slower to synthesize.
            // The long form is the same as the short form, just reordered to
            // match the function on the left (the reference).
            // Same function as the short form.
            y <= ((((((((86 * x + 73) * x + 23) * x + 69) * x + 48) * x + 52) * x + 39)) & 16'hFFFF);
        end
    end
endmodule
