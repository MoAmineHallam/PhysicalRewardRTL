module apifast__firr36__g3 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Delay line - 36 taps (tap 0 = current x)
    reg [7:0] delay_line [0:35];
    
    // Pipeline stages for partial sums
    // Stage 1: multiply and first addition
    // Stage 2-5: tree addition
    // Stage 6: final accumulation and output
    
    // First stage pipeline registers (multiply + initial pair adds)
    reg [23:0] stage1_sum [0:17]; // 18 pairs of (k+1)*tap[k] + (k+2)*tap[k+1]
    
    // Second stage pipeline registers (pair-wise addition of stage1 results)
    reg [24:0] stage2_sum [0:8]; // 9 sums
    
    // Third stage pipeline registers
    reg [25:0] stage3_sum [0:4]; // 5 sums (4+1 for odd count)
    
    // Fourth stage pipeline registers
    reg [26:0] stage4_sum [0:2]; // 3 sums
    
    // Fifth stage pipeline registers
    reg [27:0] stage5_sum [0:1]; // 2 sums
    
    // Sixth stage - final sum and output
    reg [28:0] final_sum;
    
    integer i;
    
    // Delay line update
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 36; i = i + 1)
                delay_line[i] <= 8'd0;
        end else begin
            // Shift delay line: new sample at tap 0
            delay_line[0] <= x;
            for (i = 1; i < 36; i = i + 1)
                delay_line[i] <= delay_line[i-1];
        end
    end
    
    // Stage 1: Multiply and first pair addition
    // Each tap k uses coefficient (k+1)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 18; i = i + 1)
                stage1_sum[i] <= 24'd0;
        end else begin
            // Combine pairs: (2k+1)*delay[2k] + (2k+2)*delay[2k+1]
            for (i = 0; i < 18; i = i + 1) begin
                stage1_sum[i] <= (delay_line[2*i] * (2*i+1)) + 
                                 (delay_line[2*i+1] * (2*i+2));
            end
        end
    end
    
    // Stage 2: Sum pairs of stage1 results
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 9; i = i + 1)
                stage2_sum[i] <= 25'd0;
        end else begin
            for (i = 0; i < 9; i = i + 1)
                stage2_sum[i] <= stage1_sum[2*i] + stage1_sum[2*i+1];
        end
    end
    
    // Stage 3: Sum pairs of stage2 results (5 sums needed for 9 inputs)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 5; i = i + 1)
                stage3_sum[i] <= 26'd0;
        end else begin
            stage3_sum[0] <= stage2_sum[0] + stage2_sum[1];
            stage3_sum[1] <= stage2_sum[2] + stage2_sum[3];
            stage3_sum[2] <= stage2_sum[4] + stage2_sum[5];
            stage3_sum[3] <= stage2_sum[6] + stage2_sum[7];
            stage3_sum[4] <= {1'b0, stage2_sum[8]}; // Pass through with zero extension
        end
    end
    
    // Stage 4: Sum pairs of stage3 results
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 3; i = i + 1)
                stage4_sum[i] <= 27'd0;
        end else begin
            stage4_sum[0] <= stage3_sum[0] + stage3_sum[1];
            stage4_sum[1] <= stage3_sum[2] + stage3_sum[3];
            stage4_sum[2] <= {1'b0, stage3_sum[4]}; // Pass through with zero extension
        end
    end
    
    // Stage 5: Final pair addition
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            stage5_sum[0] <= 28'd0;
            stage5_sum[1] <= 28'd0;
        end else begin
            stage5_sum[0] <= stage4_sum[0] + stage4_sum[1];
            stage5_sum[1] <= {1'b0, stage4_sum[2]}; // Pass through with zero extension
        end
    end
    
    // Stage 6: Final accumulation and output
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            final_sum <= 29'd0;
            y <= 16'd0;
        end else begin
            final_sum <= stage5_sum[0] + stage5_sum[1];
            y <= final_sum[15:0]; // Take low 16 bits
        end
    end

endmodule