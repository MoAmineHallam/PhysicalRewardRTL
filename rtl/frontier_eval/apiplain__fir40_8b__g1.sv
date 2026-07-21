module apiplain__fir40_8b__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Delay line: 40 samples, each 8 bits
    reg [7:0] delay_line [0:39];
    integer i;

    // Fixed coefficients (symmetric)
    wire [6:0] coeff [0:39];
    assign coeff[0]  = 7'd3;
    assign coeff[1]  = 7'd5;
    assign coeff[2]  = 7'd7;
    assign coeff[3]  = 7'd9;
    assign coeff[4]  = 7'd11;
    assign coeff[5]  = 7'd13;
    assign coeff[6]  = 7'd15;
    assign coeff[7]  = 7'd17;
    assign coeff[8]  = 7'd19;
    assign coeff[9]  = 7'd21;
    assign coeff[10] = 7'd23;
    assign coeff[11] = 7'd25;
    assign coeff[12] = 7'd27;
    assign coeff[13] = 7'd29;
    assign coeff[14] = 7'd31;
    assign coeff[15] = 7'd33;
    assign coeff[16] = 7'd35;
    assign coeff[17] = 7'd37;
    assign coeff[18] = 7'd39;
    assign coeff[19] = 7'd41;
    assign coeff[20] = 7'd41;
    assign coeff[21] = 7'd39;
    assign coeff[22] = 7'd37;
    assign coeff[23] = 7'd35;
    assign coeff[24] = 7'd33;
    assign coeff[25] = 7'd31;
    assign coeff[26] = 7'd29;
    assign coeff[27] = 7'd27;
    assign coeff[28] = 7'd25;
    assign coeff[29] = 7'd23;
    assign coeff[30] = 7'd21;
    assign coeff[31] = 7'd19;
    assign coeff[32] = 7'd17;
    assign coeff[33] = 7'd15;
    assign coeff[34] = 7'd13;
    assign coeff[35] = 7'd11;
    assign coeff[36] = 7'd9;
    assign coeff[37] = 7'd7;
    assign coeff[38] = 7'd5;
    assign coeff[39] = 7'd3;

    // Sum of products (needs enough bits for 40 * 255 * 41 = 418200, 19 bits)
    reg [18:0] sum;
    integer j;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 40; i = i + 1)
                delay_line[i] <= 8'd0;
            y <= 16'd0;
            sum <= 19'd0;
        end else begin
            // Shift delay line and insert new sample
            for (i = 39; i > 0; i = i - 1)
                delay_line[i] <= delay_line[i-1];
            delay_line[0] <= x;

            // Compute sum of products
            sum = 19'd0;
            for (j = 0; j < 40; j = j + 1) begin
                sum = sum + (delay_line[j] * coeff[j]);
            end

            // Output lower 16 bits
            y <= sum[15:0];
        end
    end

endmodule