module apiplain__firr36__g5 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // 36-element delay line (tap 0 = newest sample)
    reg [7:0] delay_line [0:35];
    
    // Internal signal for accumulator (wide enough to avoid overflow)
    wire [21:0] sum;
    
    integer k;
    
    // Accumulate sum of (k+1)*tap[k]
    assign sum = delay_line[0] * 1 + 
                 delay_line[1] * 2 + 
                 delay_line[2] * 3 + 
                 delay_line[3] * 4 + 
                 delay_line[4] * 5 + 
                 delay_line[5] * 6 + 
                 delay_line[6] * 7 + 
                 delay_line[7] * 8 + 
                 delay_line[8] * 9 + 
                 delay_line[9] * 10 + 
                 delay_line[10] * 11 + 
                 delay_line[11] * 12 + 
                 delay_line[12] * 13 + 
                 delay_line[13] * 14 + 
                 delay_line[14] * 15 + 
                 delay_line[15] * 16 + 
                 delay_line[16] * 17 + 
                 delay_line[17] * 18 + 
                 delay_line[18] * 19 + 
                 delay_line[19] * 20 + 
                 delay_line[20] * 21 + 
                 delay_line[21] * 22 + 
                 delay_line[22] * 23 + 
                 delay_line[23] * 24 + 
                 delay_line[24] * 25 + 
                 delay_line[25] * 26 + 
                 delay_line[26] * 27 + 
                 delay_line[27] * 28 + 
                 delay_line[28] * 29 + 
                 delay_line[29] * 30 + 
                 delay_line[30] * 31 + 
                 delay_line[31] * 32 + 
                 delay_line[32] * 33 + 
                 delay_line[33] * 34 + 
                 delay_line[34] * 35 + 
                 delay_line[35] * 36;
    
    // Update delay line and output
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear delay line
            for (k = 0; k < 36; k = k + 1) begin
                delay_line[k] <= 8'd0;
            end
            y <= 16'd0;
        end else begin
            // Shift delay line and insert new sample at tap 0
            for (k = 35; k > 0; k = k - 1) begin
                delay_line[k] <= delay_line[k-1];
            end
            delay_line[0] <= x;
            
            // Output the low 16 bits of the sum
            y <= sum[15:0];
        end
    end

endmodule