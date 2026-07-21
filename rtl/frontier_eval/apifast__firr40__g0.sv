module apifast__firr40__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // 40-element delay line (tap 0 = newest = current x)
    reg [7:0] delay [0:39];
    
    // Pipeline registers for tree accumulation
    // Stage 1: Multiply-accumulate pairs
    // Stage 2-6: Tree adder stages
    
    // Stage 1 products and partial sums (40 inputs -> 20 results)
    reg [23:0] stage1_sum [0:19];  // 24 bits to hold product + sum
    
    // Stage 2 (20 -> 10)
    reg [23:0] stage2_sum [0:9];
    
    // Stage 3 (10 -> 5)
    reg [23:0] stage3_sum [0:4];
    
    // Stage 4 (5 -> 3)
    reg [23:0] stage4_sum [0:2];
    
    // Stage 5 (3 -> 2)
    reg [23:0] stage5_sum [0:1];
    
    // Stage 6 (2 -> 1)
    reg [23:0] stage6_result;
    
    integer i;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear delay line
            for (i = 0; i < 40; i = i + 1) begin
                delay[i] <= 8'd0;
            end
            
            // Clear pipeline registers
            for (i = 0; i < 20; i = i + 1) begin
                stage1_sum[i] <= 24'd0;
            end
            for (i = 0; i < 10; i = i + 1) begin
                stage2_sum[i] <= 24'd0;
            end
            for (i = 0; i < 5; i = i + 1) begin
                stage3_sum[i] <= 24'd0;
            end
            for (i = 0; i < 3; i = i + 1) begin
                stage4_sum[i] <= 24'd0;
            end
            for (i = 0; i < 2; i = i + 1) begin
                stage5_sum[i] <= 24'd0;
            end
            stage6_result <= 24'd0;
            y <= 16'd0;
        end else begin
            // Shift delay line and insert new sample
            for (i = 39; i > 0; i = i - 1) begin
                delay[i] <= delay[i-1];
            end
            delay[0] <= x;
            
            // Stage 1: Multiply and add in pairs
            for (i = 0; i < 20; i = i + 1) begin
                // Pair: tap[2i] with coefficient (2i+1) and tap[2i+1] with coefficient (2i+2)
                stage1_sum[i] <= ({16'd0, delay[2*i]} * (2*i + 1)) + 
                                 ({16'd0, delay[2*i+1]} * (2*i + 2));
            end
            
            // Stage 2: Sum pairs
            for (i = 0; i < 10; i = i + 1) begin
                stage2_sum[i] <= stage1_sum[2*i] + stage1_sum[2*i + 1];
            end
            
            // Stage 3
            for (i = 0; i < 5; i = i + 1) begin
                stage3_sum[i] <= stage2_sum[2*i] + stage2_sum[2*i + 1];
            end
            
            // Stage 4
            stage4_sum[0] <= stage3_sum[0] + stage3_sum[1];
            stage4_sum[1] <= stage3_sum[2] + stage3_sum[3];
            stage4_sum[2] <= stage3_sum[4];  // Odd number, pass through
            
            // Stage 5
            stage5_sum[0] <= stage4_sum[0] + stage4_sum[1];
            stage5_sum[1] <= stage4_sum[2];  // Pass through
            
            // Stage 6: Final addition
            stage6_result <= stage5_sum[0] + stage5_sum[1];
            
            // Output: low 16 bits
            y <= stage6_result[15:0];
        end
    end

endmodule