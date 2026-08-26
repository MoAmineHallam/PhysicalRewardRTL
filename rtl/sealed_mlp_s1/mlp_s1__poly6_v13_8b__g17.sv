module mlp_s1__poly6_v13_8b__g17 (
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
            // (inline nested Horner, no intermediate named wires)
            y <= ((((((((86 * x + 73) * x + 23) * x + 69) * x + 48) * x + 52) * x + 39)) & 16'hFFFF);
        end
    end
endmodule
