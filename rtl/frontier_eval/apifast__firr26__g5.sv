module apifast__firr26__g5 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // 26-element delay line (registered)
    reg [7:0] taps [0:25];
    
    // Pipeline stages for partial sums
    // Stage 0 has 13 partial sums (pairs of 2 taps each)
    reg [15:0] stage0 [0:12];
    // Stage 1 has 7 partial sums
    reg [15:0] stage1 [0:6];
    // Stage 2 has 4 partial sums
    reg [15:0] stage2 [0:3];
    // Stage 3 has 2 partial sums
    reg [15:0] stage3 [0:1];
    // Stage 4 has final sum
    reg [15:0] stage4;
    
    integer i;
    
    // Delay line update and first computation stage
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear delay line
            for (i = 0; i < 26; i = i + 1) begin
                taps[i] <= 8'd0;
            end
            // Clear all pipeline stages
            for (i = 0; i < 13; i = i + 1) begin
                stage0[i] <= 16'd0;
            end
            for (i = 0; i < 7; i = i + 1) begin
                stage1[i] <= 16'd0;
            end
            for (i = 0; i < 4; i = i + 1) begin
                stage2[i] <= 16'd0;
            end
            for (i = 0; i < 2; i = i + 1) begin
                stage3[i] <= 16'd0;
            end
            stage4 <= 16'd0;
            y <= 16'd0;
        end else begin
            // Shift delay line and insert new sample
            for (i = 25; i > 0; i = i - 1) begin
                taps[i] <= taps[i-1];
            end
            taps[0] <= x;
            
            // Stage 0: Multiply each tap by its coefficient and sum pairs
            // Each operation: (k+1)*taps[k] + (k+2)*taps[k+1]
            stage0[0] <= (1 * taps[0]) + (2 * taps[1]);
            stage0[1] <= (3 * taps[2]) + (4 * taps[3]);
            stage0[2] <= (5 * taps[4]) + (6 * taps[5]);
            stage0[3] <= (7 * taps[6]) + (8 * taps[7]);
            stage0[4] <= (9 * taps[8]) + (10 * taps[9]);
            stage0[5] <= (11 * taps[10]) + (12 * taps[11]);
            stage0[6] <= (13 * taps[12]) + (14 * taps[13]);
            stage0[7] <= (15 * taps[14]) + (16 * taps[15]);
            stage0[8] <= (17 * taps[16]) + (18 * taps[17]);
            stage0[9] <= (19 * taps[18]) + (20 * taps[19]);
            stage0[10] <= (21 * taps[20]) + (22 * taps[21]);
            stage0[11] <= (23 * taps[22]) + (24 * taps[23]);
            stage0[12] <= (25 * taps[24]) + (26 * taps[25]);
        end
    end
    
    // Stage 1: Sum pairs from stage 0
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 7; i = i + 1) begin
                stage1[i] <= 16'd0;
            end
        end else begin
            stage1[0] <= stage0[0] + stage0[1];
            stage1[1] <= stage0[2] + stage0[3];
            stage1[2] <= stage0[4] + stage0[5];
            stage1[3] <= stage0[6] + stage0[7];
            stage1[4] <= stage0[8] + stage0[9];
            stage1[5] <= stage0[10] + stage0[11];
            stage1[6] <= stage0[12];  // odd one out, just pass through
        end
    end
    
    // Stage 2: Sum pairs from stage 1
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 4; i = i + 1) begin
                stage2[i] <= 16'd0;
            end
        end else begin
            stage2[0] <= stage1[0] + stage1[1];
            stage2[1] <= stage1[2] + stage1[3];
            stage2[2] <= stage1[4] + stage1[5];
            stage2[3] <= stage1[6];  // odd one out
        end
    end
    
    // Stage 3: Sum pairs from stage 2
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 2; i = i + 1) begin
                stage3[i] <= 16'd0;
            end
        end else begin
            stage3[0] <= stage2[0] + stage2[1];
            stage3[1] <= stage2[2] + stage2[3];
        end
    end
    
    // Stage 4: Final sum and output
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            stage4 <= 16'd0;
            y <= 16'd0;
        end else begin
            stage4 <= stage3[0] + stage3[1];
            y <= stage4;
        end
    end

endmodule