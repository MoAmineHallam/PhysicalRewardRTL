module base__fir6_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    reg [7:0] delay_line [5:0]; // 6 element delay line
    reg [15:0] acc_sum; // accumulator for the sum of products
    reg [15:0] coeff [5:0]; // coefficients

    // Coefficients initialization
    initial begin
        coeff[0] = 3;
        coeff[1] = 5;
        coeff[2] = 7;
        coeff[3] = 7;
        coeff[4] = 5;
        coeff[5] = 3;
    end

    always @(posedge clk) begin
        if (!rst_n) begin
            // Reset state
            acc_sum <= 0;
            delay_line[0] <= 0;
            delay_line[1] <= 0;
            delay_line[2] <= 0;
            delay_line[3] <= 0;
            delay_line[4] <= 0;
            delay_line[5] <= 0;
        end else begin
            // Shift delay line
            delay_line[5] <= delay_line[4];
            delay_line[4] <= delay_line[3];
            delay_line[3] <= delay_line[2];
            delay_line[2] <= delay_line[1];
            delay_line[1] <= delay_line[0];
            delay_line[0] <= x;

            // Calculate sum of products
            acc_sum <= coeff[0] * delay_line[5] +
                       coeff[1] * delay_line[4] +
                       coeff[2] * delay_line[3] +
                       coeff[3] * delay_line[2] +
                       coeff[4] * delay_line[1] +
                       coeff[5] * delay_line[0];
        end
    end

    assign y = acc_sum; // Output is register on posedge clk

endmodule