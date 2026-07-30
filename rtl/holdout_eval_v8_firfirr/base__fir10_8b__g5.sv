module base__fir10_8b__g5 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Define constants for coefficients
    parameter COEFF_A = 3;
    parameter COEFF_B = 5;
    parameter COEFF_C = 7;
    parameter COEFF_D = 9;
    parameter COEFF_E = 11;
    parameter COEFF_F = 11;
    parameter COEFF_G = 9;
    parameter COEFF_H = 7;
    parameter COEFF_I = 5;
    parameter COEFF_J = 3;

    reg [7:0] delay_line[0:9];
    integer i;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear state
            for (i = 0; i < 10; i = i + 1) begin
                delay_line[i] <= 8'b0;
            end
            y <= 16'b0;
        end else begin
            // Update delay line
            for (i = 9; i > 0; i = i - 1) begin
                delay_line[i] <= delay_line[i-1];
            end
            delay_line[0] <= x;

            // Calculate output
            y <= (delay_line[0] * COEFF_A) +
                 (delay_line[1] * COEFF_B) +
                 (delay_line[2] * COEFF_C) +
                 (delay_line[3] * COEFF_D) +
                 (delay_line[4] * COEFF_E) +
                 (delay_line[5] * COEFF_F) +
                 (delay_line[6] * COEFF_G) +
                 (delay_line[7] * COEFF_H) +
                 (delay_line[8] * COEFF_I) +
                 (delay_line[9] * COEFF_J);
        end
    end

endmodule