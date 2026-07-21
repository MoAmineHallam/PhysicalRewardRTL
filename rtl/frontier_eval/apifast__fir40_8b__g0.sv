module apifast__fir40_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Delay line registers (40 taps, 8-bit unsigned)
    reg [7:0] delay [0:39];
    integer i;
    
    // Pipeline registers for partial sums
    // We use a tree structure: first stage multiply and add pairs
    // Each stage reduces the number of terms by roughly half
    
    // Stage 1: 20 multiply-adds
    reg [15:0] stage1 [0:19];
    
    // Stage 2: 10 adds
    reg [15:0] stage2 [0:9];
    
    // Stage 3: 5 adds
    reg [15:0] stage3 [0:4];
    
    // Stage 4: 3 adds (5->3: 2 pairs + 1 leftover)
    reg [15:0] stage4 [0:2];
    
    // Stage 5: 2 adds (3->2: 1 pair + 1 leftover)
    reg [15:0] stage5 [0:1];
    
    // Stage 6: final add -> output
    reg [15:0] sum_final;
    
    // Coefficients (symmetric)
    // [3,5,7,9,11,13,15,17,19,21,23,25,27,29,31,33,35,37,39,41,
    //  41,39,37,35,33,31,29,27,25,23,21,19,17,15,13,11,9,7,5,3]
    // Note: Since symmetric, we could optimize further, but here we keep direct form
    
    // Function to multiply 8-bit unsigned by coefficient and return 16-bit
    function [15:0] mul_coef;
        input [7:0] sample;
        input [5:0] coef; // max coef=41, fits in 6 bits
        begin
            mul_coef = sample * coef;
        end
    endfunction
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear all state
            for (i = 0; i < 40; i = i + 1) delay[i] <= 8'd0;
            for (i = 0; i < 20; i = i + 1) stage1[i] <= 16'd0;
            for (i = 0; i < 10; i = i + 1) stage2[i] <= 16'd0;
            for (i = 0; i < 5; i = i + 1) stage3[i] <= 16'd0;
            for (i = 0; i < 3; i = i + 1) stage4[i] <= 16'd0;
            for (i = 0; i < 2; i = i + 1) stage5[i] <= 16'd0;
            sum_final <= 16'd0;
            y <= 16'd0;
        end else begin
            // Shift delay line and insert new sample
            for (i = 39; i > 0; i = i - 1) delay[i] <= delay[i-1];
            delay[0] <= x;
            
            // Stage 1: multiply and add pairs
            // Pair (0,39): coef 3,3 ; (1,38): 5,5 ... (19,20): 41,41
            stage1[0] <= mul_coef(delay[0], 3) + mul_coef(delay[39], 3);
            stage1[1] <= mul_coef(delay[1], 5) + mul_coef(delay[38], 5);
            stage1[2] <= mul_coef(delay[2], 7) + mul_coef(delay[37], 7);
            stage1[3] <= mul_coef(delay[3], 9) + mul_coef(delay[36], 9);
            stage1[4] <= mul_coef(delay[4], 11) + mul_coef(delay[35], 11);
            stage1[5] <= mul_coef(delay[5], 13) + mul_coef(delay[34], 13);
            stage1[6] <= mul_coef(delay[6], 15) + mul_coef(delay[33], 15);
            stage1[7] <= mul_coef(delay[7], 17) + mul_coef(delay[32], 17);
            stage1[8] <= mul_coef(delay[8], 19) + mul_coef(delay[31], 19);
            stage1[9] <= mul_coef(delay[9], 21) + mul_coef(delay[30], 21);
            stage1[10] <= mul_coef(delay[10], 23) + mul_coef(delay[29], 23);
            stage1[11] <= mul_coef(delay[11], 25) + mul_coef(delay[28], 25);
            stage1[12] <= mul_coef(delay[12], 27) + mul_coef(delay[27], 27);
            stage1[13] <= mul_coef(delay[13], 29) + mul_coef(delay[26], 29);
            stage1[14] <= mul_coef(delay[14], 31) + mul_coef(delay[25], 31);
            stage1[15] <= mul_coef(delay[15], 33) + mul_coef(delay[24], 33);
            stage1[16] <= mul_coef(delay[16], 35) + mul_coef(delay[23], 35);
            stage1[17] <= mul_coef(delay[17], 37) + mul_coef(delay[22], 37);
            stage1[18] <= mul_coef(delay[18], 39) + mul_coef(delay[21], 39);
            stage1[19] <= mul_coef(delay[19], 41) + mul_coef(delay[20], 41);
            
            // Stage 2: add pairs from stage1 (20 -> 10)
            stage2[0] <= stage1[0] + stage1[1];
            stage2[1] <= stage1[2] + stage1[3];
            stage2[2] <= stage1[4] + stage1[5];
            stage2[3] <= stage1[6] + stage1[7];
            stage2[4] <= stage1[8] + stage1[9];
            stage2[5] <= stage1[10] + stage1[11];
            stage2[6] <= stage1[12] + stage1[13];
            stage2[7] <= stage1[14] + stage1[15];
            stage2[8] <= stage1[16] + stage1[17];
            stage2[9] <= stage1[18] + stage1[19];
            
            // Stage 3: add pairs from stage2 (10 -> 5)
            stage3[0] <= stage2[0] + stage2[1];
            stage3[1] <= stage2[2] + stage2[3];
            stage3[2] <= stage2[4] + stage2[5];
            stage3[3] <= stage2[6] + stage2[7];
            stage3[4] <= stage2[8] + stage2[9];
            
            // Stage 4: add pairs from stage3 (5 -> 3)
            stage4[0] <= stage3[0] + stage3[1];
            stage4[1] <= stage3[2] + stage3[3];
            stage4[2] <= stage3[4];
            
            // Stage 5: add pairs from stage4 (3 -> 2)
            stage5[0] <= stage4[0] + stage4[1];
            stage5[1] <= stage4[2];
            
            // Stage 6: final addition
            sum_final <= stage5[0] + stage5[1];
            
            // Output low 16 bits
            y <= sum_final[15:0];
        end
    end

endmodule