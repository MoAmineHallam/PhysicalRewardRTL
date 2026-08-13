module base__fir18_8b__g2 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    parameter COEF0 = 3;
    parameter COEF1 = 5;
    parameter COEF2 = 7;
    parameter COEF3 = 9;
    parameter COEF4 = 11;
    parameter COEF5 = 13;
    parameter COEF6 = 15;
    parameter COEF7 = 17;
    parameter COEF8 = 19;
    parameter COEF9 = 19;
    parameter COEF10 = 17;
    parameter COEF11 = 15;
    parameter COEF12 = 13;
    parameter COEF13 = 11;
    parameter COEF14 = 9;
    parameter COEF15 = 7;
    parameter COEF16 = 5;
    parameter COEF17 = 3;

    reg [7:0] samples [0:17];
    integer i;

    always @(posedge clk) begin
        if (!rst_n) begin
            y <= 0;
            for (i = 0; i < 18; i = i + 1) begin
                samples[i] <= 0;
            end
        end else begin
            samples[0] <= x;
            for (i = 1; i < 18; i = i + 1) begin
                samples[i] <= samples[i-1];
            end
            y <= (x * COEF0)
                + (samples[0] * COEF1)
                + (samples[1] * COEF2)
                + (samples[2] * COEF3)
                + (samples[3] * COEF4)
                + (samples[4] * COEF5)
                + (samples[5] * COEF6)
                + (samples[6] * COEF7)
                + (samples[7] * COEF8)
                + (samples[8] * COEF9)
                + (samples[9] * COEF10)
                + (samples[10] * COEF11)
                + (samples[11] * COEF12)
                + (samples[12] * COEF13)
                + (samples[13] * COEF14)
                + (samples[14] * COEF15)
                + (samples[15] * COEF16)
                + (samples[16] * COEF17);
        end
    end

endmodule