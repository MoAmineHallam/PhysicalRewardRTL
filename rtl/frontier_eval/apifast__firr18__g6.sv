module apifast__firr18__g6 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Delay line: 18 taps (tap 0 = newest sample)
    reg [7:0] tap [0:17];
    
    // Pipeline registers for partial sums and products
    // Stage 1: multiply and accumulate pairs
    reg [15:0] sum_stage1 [0:8]; // 9 pairs (0-1, 2-3, ... 16-17)
    
    // Stage 2: sum of pairs
    reg [15:0] sum_stage2 [0:4]; // 5 groups (0-1+2-3, ...)
    
    // Stage 3: further reduction
    reg [15:0] sum_stage3 [0:2]; // 3 groups
    
    // Stage 4: final reduction
    reg [15:0] sum_stage4 [0:1]; // 2 groups
    
    // Stage 5: final sum
    reg [15:0] sum_final;
    
    integer i;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear all delay line taps
            for (i = 0; i < 18; i = i + 1)
                tap[i] <= 8'd0;
            
            // Clear all pipeline registers
            for (i = 0; i < 9; i = i + 1)
                sum_stage1[i] <= 16'd0;
            for (i = 0; i < 5; i = i + 1)
                sum_stage2[i] <= 16'd0;
            for (i = 0; i < 3; i = i + 1)
                sum_stage3[i] <= 16'd0;
            for (i = 0; i < 2; i = i + 1)
                sum_stage4[i] <= 16'd0;
            sum_final <= 16'd0;
            y <= 16'd0;
        end else begin
            // Shift delay line and insert new sample
            for (i = 17; i > 0; i = i - 1)
                tap[i] <= tap[i-1];
            tap[0] <= x;
            
            // Stage 1: multiply each tap by its coefficient (k+1) and sum pairs
            // Coefficients: tap0*1, tap1*2, tap2*3, tap3*4, ...
            // Pair 0: tap0*1 + tap1*2
            sum_stage1[0] <= (tap[0] * 9'd1) + (tap[1] * 9'd2);
            sum_stage1[1] <= (tap[2] * 9'd3) + (tap[3] * 9'd4);
            sum_stage1[2] <= (tap[4] * 9'd5) + (tap[5] * 9'd6);
            sum_stage1[3] <= (tap[6] * 9'd7) + (tap[7] * 9'd8);
            sum_stage1[4] <= (tap[8] * 9'd9) + (tap[9] * 9'd10);
            sum_stage1[5] <= (tap[10] * 9'd11) + (tap[11] * 9'd12);
            sum_stage1[6] <= (tap[12] * 9'd13) + (tap[13] * 9'd14);
            sum_stage1[7] <= (tap[14] * 9'd15) + (tap[15] * 9'd16);
            sum_stage1[8] <= (tap[16] * 9'd17) + (tap[17] * 9'd18);
            
            // Stage 2: sum pairs from stage 1
            sum_stage2[0] <= sum_stage1[0] + sum_stage1[1];
            sum_stage2[1] <= sum_stage1[2] + sum_stage1[3];
            sum_stage2[2] <= sum_stage1[4] + sum_stage1[5];
            sum_stage2[3] <= sum_stage1[6] + sum_stage1[7];
            sum_stage2[4] <= sum_stage1[8]; // odd one out
            
            // Stage 3: further reduction
            sum_stage3[0] <= sum_stage2[0] + sum_stage2[1];
            sum_stage3[1] <= sum_stage2[2] + sum_stage2[3];
            sum_stage3[2] <= sum_stage2[4]; // carry forward
            
            // Stage 4: final pair reduction
            sum_stage4[0] <= sum_stage3[0] + sum_stage3[1];
            sum_stage4[1] <= sum_stage3[2]; // carry forward
            
            // Stage 5: final sum and output
            sum_final <= sum_stage4[0] + sum_stage4[1];
            y <= sum_final;
        end
    end

endmodule