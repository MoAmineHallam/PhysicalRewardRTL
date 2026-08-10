module base__poly4_v6_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    always @(posedge clk) begin
        if (!rst_n) begin
            y <= 0; // clear y
        end else begin
            // Compute the polynomial using Horner's method
            y <= (((((65 * x + 29) * x + 88) * x + 44) * x + 17) & 16'hFFFF);
        end
    end

endmodule