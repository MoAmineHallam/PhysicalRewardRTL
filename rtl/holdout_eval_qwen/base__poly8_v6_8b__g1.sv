module base__poly8_v6_8b__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

reg [15:0] temp;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        y <= 16'b0;
    end else begin
        // Coefficients of the polynomial in order: c0, c1, ..., c8
        reg [15:0] coeffs [0:8];
        integer i;

        coeffs[0] = 92;
        coeffs[1] = 96;
        coeffs[2] = 7;
        coeffs[3] = 62;
        coeffs[4] = 54;
        coeffs[5] = 61;
        coeffs[6] = 77;
        coeffs[7] = 51;
        coeffs[8] = 45;

        temp = coeffs[0];
        for (i = 1; i <= 8; i = i + 1) begin
            temp = (temp * x) + coeffs[i];
        end

        y <= temp & 16'hFFFF;  // Keep only the lower 16 bits
    end
end

endmodule