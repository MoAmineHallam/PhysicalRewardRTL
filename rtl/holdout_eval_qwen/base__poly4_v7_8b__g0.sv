module base__poly4_v7_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

reg [15:0] temp_y;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        y <= 16'b0;
    end else begin
        // Horner's method for evaluating the polynomial 50 + 21*x + 17*x^2 + 36*x^3 + 24*x^4 mod 2^16
        temp_y <= 50 + ((21 + ((17 + (36 + (24 * x)) * x) * x)) * x);
        y <= temp_y[15:0]; // Only keep the lower 16 bits
    end
end

endmodule