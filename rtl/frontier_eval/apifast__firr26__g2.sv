module apifast__firr26__g2 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Delay line (tap 0 = newest sample)
    reg [7:0] delay_line [0:25];
    
    // Pipeline registers for the adder tree
    // Stage 1: multiply-accumulate pairs (13 pairs for 26 taps)
    reg [15:0] stage1_sum [0:12];
    
    // Stage 2: sum 13 partials into 7
    reg [15:0] stage2_sum [0:6];
    
    // Stage 3: sum 7 partials into 4
    reg [15:0] stage3_sum [0:3];
    
    // Stage 4: sum 4 partials into 2
    reg [15:0] stage4_sum [0:1];
    
    // Stage 5: final sum
    reg [15:0] stage5_sum;
    
    integer i;
    
    // Shift delay line and load new sample
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 26; i = i + 1) begin
                delay_line[i] <= 8'd0;
            end
        end else begin
            // Shift: tap[0] gets new x, tap[k] gets previous tap[k-1]
            delay_line[0] <= x;
            for (i = 1; i < 26; i = i + 1) begin
                delay_line[i] <= delay_line[i-1];
            end
        end
    end
    
    // Stage 1: Multiply by coefficient (k+1) and sum in pairs
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 13; i = i + 1) begin
                stage1_sum[i] <= 16'd0;
            end
        end else begin
            // Pair taps (0,1), (2,3), ..., (24,25)
            for (i = 0; i < 13; i = i + 1) begin
                stage1_sum[i] <= (delay_line[2*i]   * (2*i+1)) + 
                                 (delay_line[2*i+1] * (2*i+2));
            end
        end
    end
    
    // Stage 2: Sum 13 partials into 7
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 7; i = i + 1) begin
                stage2_sum[i] <= 16'd0;
            end
        end else begin
            stage2_sum[0] <= stage1_sum[0] + stage1_sum[1];
            stage2_sum[1] <= stage1_sum[2] + stage1_sum[3];
            stage2_sum[2] <= stage1_sum[4] + stage1_sum[5];
            stage2_sum[3] <= stage1_sum[6] + stage1_sum[7];
            stage2_sum[4] <= stage1_sum[8] + stage1_sum[9];
            stage2_sum[5] <= stage1_sum[10] + stage1_sum[11];
            stage2_sum[6] <= stage1_sum[12];  // Odd one out
        end
    end
    
    // Stage 3: Sum 7 partials into 4
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 4; i = i + 1) begin
                stage3_sum[i] <= 16'd0;
            end
        end else begin
            stage3_sum[0] <= stage2_sum[0] + stage2_sum[1];
            stage3_sum[1] <= stage2_sum[2] + stage2_sum[3];
            stage3_sum[2] <= stage2_sum[4] + stage2_sum[5];
            stage3_sum[3] <= stage2_sum[6];  // Odd one out
        end
    end
    
    // Stage 4: Sum 4 partials into 2
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 2; i = i + 1) begin
                stage4_sum[i] <= 16'd0;
            end
        end else begin
            stage4_sum[0] <= stage3_sum[0] + stage3_sum[1];
            stage4_sum[1] <= stage3_sum[2] + stage3_sum[3];
        end
    end
    
    // Stage 5: Final sum
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            stage5_sum <= 16'd0;
        end else begin
            stage5_sum <= stage4_sum[0] + stage4_sum[1];
        end
    end
    
    // Output register (stage 6)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            y <= 16'd0;
        end else begin
            y <= stage5_sum;
        end
    end

endmodule