module apiplain__fir36_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // 36-element delay line (8-bit unsigned samples)
    reg [7:0] delay_line [0:35];
    
    // Fixed coefficients as given
    // localparam declarations for readability (optional)
    wire [5:0] coeffs [0:35];
    assign coeffs[0]  = 6'd3;
    assign coeffs[1]  = 6'd5;
    assign coeffs[2]  = 6'd7;
    assign coeffs[3]  = 6'd9;
    assign coeffs[4]  = 6'd11;
    assign coeffs[5]  = 6'd13;
    assign coeffs[6]  = 6'd15;
    assign coeffs[7]  = 6'd17;
    assign coeffs[8]  = 6'd19;
    assign coeffs[9]  = 6'd21;
    assign coeffs[10] = 6'd23;
    assign coeffs[11] = 6'd25;
    assign coeffs[12] = 6'd27;
    assign coeffs[13] = 6'd29;
    assign coeffs[14] = 6'd31;
    assign coeffs[15] = 6'd33;
    assign coeffs[16] = 6'd35;
    assign coeffs[17] = 6'd37;
    assign coeffs[18] = 6'd37;
    assign coeffs[19] = 6'd35;
    assign coeffs[20] = 6'd33;
    assign coeffs[21] = 6'd31;
    assign coeffs[22] = 6'd29;
    assign coeffs[23] = 6'd27;
    assign coeffs[24] = 6'd25;
    assign coeffs[25] = 6'd23;
    assign coeffs[26] = 6'd21;
    assign coeffs[27] = 6'd19;
    assign coeffs[28] = 6'd17;
    assign coeffs[29] = 6'd15;
    assign coeffs[30] = 6'd13;
    assign coeffs[31] = 6'd11;
    assign coeffs[32] = 6'd9;
    assign coeffs[33] = 6'd7;
    assign coeffs[34] = 6'd5;
    assign coeffs[35] = 6'd3;
    
    // Internal product sum (wide enough to avoid overflow before truncation)
    // Max sample = 255, max coeff = 37 => max product = 9435
    // Sum of 36 such products max = 36 * 9435 = 339660, fits in 19 bits.
    reg [18:0] sum;
    integer i;
    
    // Sequential process
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear delay line
            for (i = 0; i < 36; i = i + 1) begin
                delay_line[i] <= 8'd0;
            end
            sum <= 19'd0;
            y <= 16'd0;
        end else begin
            // Shift delay line and insert new sample
            // shifting from tap 34 down to 0, then place x at tap 0
            for (i = 35; i > 0; i = i - 1) begin
                delay_line[i] <= delay_line[i-1];
            end
            delay_line[0] <= x;
            
            // Compute sum of products
            sum <= delay_line[0] * coeffs[0] 
                 + delay_line[1] * coeffs[1] 
                 + delay_line[2] * coeffs[2] 
                 + delay_line[3] * coeffs[3] 
                 + delay_line[4] * coeffs[4] 
                 + delay_line[5] * coeffs[5] 
                 + delay_line[6] * coeffs[6] 
                 + delay_line[7] * coeffs[7] 
                 + delay_line[8] * coeffs[8] 
                 + delay_line[9] * coeffs[9] 
                 + delay_line[10] * coeffs[10] 
                 + delay_line[11] * coeffs[11] 
                 + delay_line[12] * coeffs[12] 
                 + delay_line[13] * coeffs[13] 
                 + delay_line[14] * coeffs[14] 
                 + delay_line[15] * coeffs[15] 
                 + delay_line[16] * coeffs[16] 
                 + delay_line[17] * coeffs[17] 
                 + delay_line[18] * coeffs[18] 
                 + delay_line[19] * coeffs[19] 
                 + delay_line[20] * coeffs[20] 
                 + delay_line[21] * coeffs[21] 
                 + delay_line[22] * coeffs[22] 
                 + delay_line[23] * coeffs[23] 
                 + delay_line[24] * coeffs[24] 
                 + delay_line[25] * coeffs[25] 
                 + delay_line[26] * coeffs[26] 
                 + delay_line[27] * coeffs[27] 
                 + delay_line[28] * coeffs[28] 
                 + delay_line[29] * coeffs[29] 
                 + delay_line[30] * coeffs[30] 
                 + delay_line[31] * coeffs[31] 
                 + delay_line[32] * coeffs[32] 
                 + delay_line[33] * coeffs[33] 
                 + delay_line[34] * coeffs[34] 
                 + delay_line[35] * coeffs[35];
            
            // Output low 16 bits of sum
            y <= sum[15:0];
        end
    end

endmodule