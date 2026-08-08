module base__poly4_v7_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    reg [15:0] coeff_0 = 24;
    reg [15:0] coeff_1 = 36;
    reg [15:0] coeff_2 = 17;
    reg [15:0] coeff_3 = 21;
    reg [15:0] coeff_4 = 50;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            y <= 16'b0;
        end
        else begin
            // Horner's method for evaluating polynomial
            y <= (((((coeff_0 * x + coeff_1) * x + coeff_2) * x + coeff_3) * x + coeff_4) & 16'hffff);
        end
    end

endmodule