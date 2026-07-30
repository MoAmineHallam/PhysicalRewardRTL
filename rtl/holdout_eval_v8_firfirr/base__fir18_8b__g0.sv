module base__fir18_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    reg [7:0] delay_line [0:17];
    reg [15:0] coeff [0:17];
    integer i;

    always @ (posedge clk)
    begin
        if (!rst_n)
        begin
            for (i = 0; i < 18; i = i + 1)
                delay_line[i] <= 0;
            y <= 0;
        end
        else
        begin
            // Shift the delay line by one sample and add the new sample to the first place
            delay_line[17] <= delay_line[16];
            delay_line[16] <= delay_line[15];
            delay_line[15] <= delay_line[14];
            delay_line[14] <= delay_line[13];
            delay_line[13] <= delay_line[12];
            delay_line[12] <= delay_line[11];
            delay_line[11] <= delay_line[10];
            delay_line[10] <= delay_line[9];
            delay_line[9] <= delay_line[8];
            delay_line[8] <= delay_line[7];
            delay_line[7] <= delay_line[6];
            delay_line[6] <= delay_line[5];
            delay_line[5] <= delay_line[4];
            delay_line[4] <= delay_line[3];
            delay_line[3] <= delay_line[2];
            delay_line[2] <= delay_line[1];
            delay_line[1] <= delay_line[0];
            delay_line[0] <= x;

            // Multiply each sample by its coefficient and add these products together
            coeff[0] <= 3;
            coeff[1] <= 5;
            coeff[2] <= 7;
            coeff[3] <= 9;
            coeff[4] <= 11;
            coeff[5] <= 13;
            coeff[6] <= 15;
            coeff[7] <= 17;
            coeff[8] <= 19;
            coeff[9] <= 19;
            coeff[10] <= 17;
            coeff[11] <= 15;
            coeff[12] <= 13;
            coeff[13] <= 11;
            coeff[14] <= 9;
            coeff[15] <= 7;
            coeff[16] <= 5;
            coeff[17] <= 3;

            y <= (delay_line[0] * coeff[0]) + (delay_line[1] * coeff[1]) + (delay_line[2] * coeff[2]) +
                (delay_line[3] * coeff[3]) + (delay_line[4] * coeff[4]) + (delay_line[5] * coeff[5]) +
                (delay_line[6] * coeff[6]) + (delay_line[7] * coeff[7]) + (delay_line[8] * coeff[8]) +
                (delay_line[9] * coeff[9]) + (delay_line[10] * coeff[10]) + (delay_line[11] * coeff[11]) +
                (delay_line[12] * coeff[12]) + (delay_line[13] * coeff[13]) + (delay_line[14] * coeff[14]) +
                (delay_line[15] * coeff[15]) + (delay_line[16] * coeff[16]) + (delay_line[17] * coeff[17]);
        end
    end

endmodule