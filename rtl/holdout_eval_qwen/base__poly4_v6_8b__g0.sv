module base__poly4_v6_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

reg [15:0] tmp;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        y <= 16'b0;
        tmp <= 16'b0;
    end else begin
        // Evaluate the polynomial using Horner's rule:
        // y = ((65 * x + 29) * x + 88) * x + 44) * x + 17
        tmp <= (((((65 * x[7:0]) + 29) * x[7:0] + 88) * x[7:0] + 44) * x[7:0] + 17);
        y <= tmp & 16'hFFFF;  // Ensure only the lower 16 bits are used.
    end
end

endmodule