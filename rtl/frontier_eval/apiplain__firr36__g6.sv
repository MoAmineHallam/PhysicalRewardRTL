module apiplain__firr36__g6 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // 36-element delay line (tap 0 = newest = current x)
    reg [7:0] taps [0:35];
    
    // Internal sum (needs enough bits: 8 bits * max coeff 36 * 36 taps)
    // Max sum = 36 * 36 * 255 = 330,480, which needs 19 bits
    // We'll use 19 bits for intermediate computation
    wire [18:0] sum;
    integer k;
    
    // Compute the sum: y = sum over k=0..35 of (k+1)*tap[k]
    // Only keep low 16 bits
    assign sum = taps[0] * 1 + 
                 taps[1] * 2 + 
                 taps[2] * 3 + 
                 taps[3] * 4 + 
                 taps[4] * 5 + 
                 taps[5] * 6 + 
                 taps[6] * 7 + 
                 taps[7] * 8 + 
                 taps[8] * 9 + 
                 taps[9] * 10 + 
                 taps[10] * 11 + 
                 taps[11] * 12 + 
                 taps[12] * 13 + 
                 taps[13] * 14 + 
                 taps[14] * 15 + 
                 taps[15] * 16 + 
                 taps[16] * 17 + 
                 taps[17] * 18 + 
                 taps[18] * 19 + 
                 taps[19] * 20 + 
                 taps[20] * 21 + 
                 taps[21] * 22 + 
                 taps[22] * 23 + 
                 taps[23] * 24 + 
                 taps[24] * 25 + 
                 taps[25] * 26 + 
                 taps[26] * 27 + 
                 taps[27] * 28 + 
                 taps[28] * 29 + 
                 taps[29] * 30 + 
                 taps[30] * 31 + 
                 taps[31] * 32 + 
                 taps[32] * 33 + 
                 taps[33] * 34 + 
                 taps[34] * 35 + 
                 taps[35] * 36;
    
    // Sequential logic
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear all taps
            for (k = 0; k < 36; k = k + 1) begin
                taps[k] <= 8'd0;
            end
            y <= 16'd0;
        end else begin
            // Shift delay line: oldest to newest, then insert new sample
            // tap[35] gets tap[34], tap[34] gets tap[33], ..., tap[1] gets tap[0], tap[0] gets x
            for (k = 35; k > 0; k = k - 1) begin
                taps[k] <= taps[k-1];
            end
            taps[0] <= x;
            
            // Output registered sum (low 16 bits)
            y <= sum[15:0];
        end
    end

endmodule