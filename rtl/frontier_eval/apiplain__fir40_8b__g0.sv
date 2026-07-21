module apiplain__fir40_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // 40-element delay line (shift register) of past samples
    reg [7:0] delay_line [0:39];
    
    // Fixed coefficients [3,5,7,9,11,13,15,17,19,21,23,25,27,29,31,33,35,37,39,41,
    //                    41,39,37,35,33,31,29,27,25,23,21,19,17,15,13,11,9,7,5,3]
    wire [6:0] coeffs [0:39];
    assign coeffs[0]  = 7'd3;
    assign coeffs[1]  = 7'd5;
    assign coeffs[2]  = 7'd7;
    assign coeffs[3]  = 7'd9;
    assign coeffs[4]  = 7'd11;
    assign coeffs[5]  = 7'd13;
    assign coeffs[6]  = 7'd15;
    assign coeffs[7]  = 7'd17;
    assign coeffs[8]  = 7'd19;
    assign coeffs[9]  = 7'd21;
    assign coeffs[10] = 7'd23;
    assign coeffs[11] = 7'd25;
    assign coeffs[12] = 7'd27;
    assign coeffs[13] = 7'd29;
    assign coeffs[14] = 7'd31;
    assign coeffs[15] = 7'd33;
    assign coeffs[16] = 7'd35;
    assign coeffs[17] = 7'd37;
    assign coeffs[18] = 7'd39;
    assign coeffs[19] = 7'd41;
    assign coeffs[20] = 7'd41;
    assign coeffs[21] = 7'd39;
    assign coeffs[22] = 7'd37;
    assign coeffs[23] = 7'd35;
    assign coeffs[24] = 7'd33;
    assign coeffs[25] = 7'd31;
    assign coeffs[26] = 7'd29;
    assign coeffs[27] = 7'd27;
    assign coeffs[28] = 7'd25;
    assign coeffs[29] = 7'd23;
    assign coeffs[30] = 7'd21;
    assign coeffs[31] = 7'd19;
    assign coeffs[32] = 7'd17;
    assign coeffs[33] = 7'd15;
    assign coeffs[34] = 7'd13;
    assign coeffs[35] = 7'd11;
    assign coeffs[36] = 7'd9;
    assign coeffs[37] = 7'd7;
    assign coeffs[38] = 7'd5;
    assign coeffs[39] = 7'd3;

    // Internal product sum (wide enough to hold full result)
    wire [15:0] sum_low;
    reg [25:0] product_sum;

    integer i;

    // Shift register and product accumulation
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear delay line and output
            for (i = 0; i < 40; i = i + 1)
                delay_line[i] <= 8'd0;
            y <= 16'd0;
            product_sum <= 26'd0;
        end else begin
            // Shift in new sample
            delay_line[0] <= x;
            for (i = 1; i < 40; i = i + 1)
                delay_line[i] <= delay_line[i-1];
            
            // Compute sum of products
            product_sum = 26'd0;
            for (i = 0; i < 40; i = i + 1)
                product_sum = product_sum + (delay_line[i] * coeffs[i]);
            
            // Output low 16 bits
            y <= product_sum[15:0];
        end
    end

endmodule