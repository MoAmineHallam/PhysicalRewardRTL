module base__fir26_8b__g3 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    reg [7:0] delay_line [0:25];
    integer   i;
    reg [15:0] coeffs [0:25];

    // Initialise the coefficients
    initial begin
        coeffs[0] = 3;
        coeffs[1] = 5;
        coeffs[2] = 7;
        coeffs[3] = 9;
        coeffs[4] = 11;
        coeffs[5] = 13;
        coeffs[6] = 15;
        coeffs[7] = 17;
        coeffs[8] = 19;
        coeffs[9] = 21;
        coeffs[10] = 23;
        coeffs[11] = 25;
        coeffs[12] = 27;
        coeffs[13] = 27;
        coeffs[14] = 25;
        coeffs[15] = 23;
        coeffs[16] = 21;
        coeffs[17] = 19;
        coeffs[18] = 17;
        coeffs[19] = 15;
        coeffs[20] = 13;
        coeffs[21] = 11;
        coeffs[22] = 9;
        coeffs[23] = 7;
        coeffs[24] = 5;
        coeffs[25] = 3;
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            y <= 16'b0;
            for (i = 0; i < 26; i = i + 1) begin
                delay_line[i] <= 8'b0;
            end
        end
        else begin
            // Shift the delay line and new value into it
            delay_line[0] <= x;
            for (i = 1; i < 26; i = i + 1) begin
                delay_line[i] <= delay_line[i-1];
            end

            // Perform the multiplication of the coefficients and delay line and sum into the output
            y <= coeffs[0]*delay_line[0] + coeffs[1]*delay_line[1] + coeffs[2]*delay_line[2] + coeffs[3]*delay_line[3] +
                coeffs[4]*delay_line[4] + coeffs[5]*delay_line[5] + coeffs[6]*delay_line[6] + coeffs[7]*delay_line[7] +
                coeffs[8]*delay_line[8] + coeffs[9]*delay_line[9] + coeffs[10]*delay_line[10] + coeffs[11]*delay_line[11] +
                coeffs[12]*delay_line[12] + coeffs[13]*delay_line[13] + coeffs[14]*delay_line[14] + coeffs[15]*delay_line[15] +
                coeffs[16]*delay_line[16] + coeffs[17]*delay_line[17] + coeffs[18]*delay_line[18] + coeffs[19]*delay_line[19] +
                coeffs[20]*delay_line[20] + coeffs[21]*delay_line[21] + coeffs[22]*delay_line[22] + coeffs[23]*delay_line[23] +
                coeffs[24]*delay_line[24] + coeffs[25]*delay_line[25];
        end
    end

endmodule