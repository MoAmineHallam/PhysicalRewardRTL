module base__poly7_v4_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Use Horner's method to compute polynomial with coefficients [20, 77, 15, 31, 25, 28, 45, 10]
    // Evaluate each coefficient at x
    // Keep only the low 16 bits of the result
    // Register the result into y
    always @(posedge clk) begin
        if (!rst_n) begin
            y <= 0;
        end else begin
            y <= (((((((20 * x + 77) * x + 15) * x + 31) * x + 25) * x + 28) * x + 45) * x + 10) & 16'hffff;
        end
    end

endmodule