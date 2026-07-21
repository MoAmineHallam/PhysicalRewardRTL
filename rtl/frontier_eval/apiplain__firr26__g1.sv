module apiplain__firr26__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Delay line of past samples (26 taps)
    reg [7:0] tap [0:25];
    
    // Internal signal for the sum (sufficient width to avoid overflow)
    wire [20:0] sum;
    
    integer k;
    
    // Compute the sum of (k+1)*tap[k] for k=0..25
    // Maximum value: sum of (k+1)*255 for k=0..25 = 255 * (26*27/2) = 255*351 = 89505
    // This fits in 17 bits, but we use 21 bits for safety
    assign sum = tap[0] * 1 + tap[1] * 2 + tap[2] * 3 + tap[3] * 4 + 
                 tap[4] * 5 + tap[5] * 6 + tap[6] * 7 + tap[7] * 8 +
                 tap[8] * 9 + tap[9] * 10 + tap[10] * 11 + tap[11] * 12 +
                 tap[12] * 13 + tap[13] * 14 + tap[14] * 15 + tap[15] * 16 +
                 tap[16] * 17 + tap[17] * 18 + tap[18] * 19 + tap[19] * 20 +
                 tap[20] * 21 + tap[21] * 22 + tap[22] * 23 + tap[23] * 24 +
                 tap[24] * 25 + tap[25] * 26;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear all state
            for (k = 0; k < 26; k = k + 1) begin
                tap[k] <= 8'd0;
            end
            y <= 16'd0;
        end else begin
            // Shift delay line and insert new sample
            for (k = 25; k > 0; k = k - 1) begin
                tap[k] <= tap[k-1];
            end
            tap[0] <= x;
            
            // Register output (low 16 bits of sum)
            y <= sum[15:0];
        end
    end

endmodule