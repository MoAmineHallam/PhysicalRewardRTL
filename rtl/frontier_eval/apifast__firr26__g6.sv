module apifast__firr26__g6 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Delay line (tap 0 = newest)
    reg [7:0] delay_line [0:25];
    
    // Pipeline registers for the adder tree
    // Stage 1: multiply-accumulate pairs
    reg [15:0] stage1_partial [0:12]; // 13 products after pairwise multiplication
    
    // Stage 2 through Stage 5: binary adder tree
    reg [15:0] stage2 [0:6];
    reg [15:0] stage3 [0:3];
    reg [15:0] stage4 [0:1];
    reg [15:0] stage5;
    
    integer i;
    
    // Delay line shift on every cycle
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 26; i = i + 1)
                delay_line[i] <= 8'd0;
        end else begin
            // Shift delay line: new sample goes to tap 0
            delay_line[0] <= x;
            for (i = 1; i < 26; i = i + 1)
                delay_line[i] <= delay_line[i-1];
        end
    end
    
    // Stage 1: Compute (k+1)*tap[k] for all taps
    // Coefficient k+1 = 1..26, multiply by tap value
    // Pair them up to keep one multiply per pipeline stage
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 13; i = i + 1)
                stage1_partial[i] <= 16'd0;
        end else begin
            // Pair taps (0&1), (2&3), ..., (24&25)
            // Tap 0: coeff 1, Tap 1: coeff 2  -> 1*x[0] + 2*x[1]
            stage1_partial[0] <= {8'd0, delay_line[0]} + {7'd0, delay_line[1], 1'd0}; // 1*x + 2*x
            stage1_partial[1] <= {7'd0, delay_line[2], 1'd0} + {6'd0, delay_line[3], 2'd0}; // 3*x + 4*x
            stage1_partial[2] <= {6'd0, delay_line[4], 2'd0} + {6'd0, delay_line[5], 2'd0} + delay_line[5]; // 5*x + 6*x (5=4+1, 6=4+2)
            // Actually let's use proper multiplication, which synthesizer will optimize
            // For clarity, compute each sum directly
            stage1_partial[0] <= (delay_line[0] * 1) + (delay_line[1] * 2);
            stage1_partial[1] <= (delay_line[2] * 3) + (delay_line[3] * 4);
            stage1_partial[2] <= (delay_line[4] * 5) + (delay_line[5] * 6);
            stage1_partial[3] <= (delay_line[6] * 7) + (delay_line[7] * 8);
            stage1_partial[4] <= (delay_line[8] * 9) + (delay_line[9] * 10);
            stage1_partial[5] <= (delay_line[10] * 11) + (delay_line[11] * 12);
            stage1_partial[6] <= (delay_line[12] * 13) + (delay_line[13] * 14);
            stage1_partial[7] <= (delay_line[14] * 15) + (delay_line[15] * 16);
            stage1_partial[8] <= (delay_line[16] * 17) + (delay_line[17] * 18);
            stage1_partial[9] <= (delay_line[18] * 19) + (delay_line[19] * 20);
            stage1_partial[10] <= (delay_line[20] * 21) + (delay_line[21] * 22);
            stage1_partial[11] <= (delay_line[22] * 23) + (delay_line[23] * 24);
            stage1_partial[12] <= (delay_line[24] * 25) + (delay_line[25] * 26);
        end
    end
    
    // Stage 2: Add pairs from stage 1
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 7; i = i + 1)
                stage2[i] <= 16'd0;
        end else begin
            stage2[0] <= stage1_partial[0] + stage1_partial[1];
            stage2[1] <= stage1_partial[2] + stage1_partial[3];
            stage2[2] <= stage1_partial[4] + stage1_partial[5];
            stage2[3] <= stage1_partial[6] + stage1_partial[7];
            stage2[4] <= stage1_partial[8] + stage1_partial[9];
            stage2[5] <= stage1_partial[10] + stage1_partial[11];
            stage2[6] <= stage1_partial[12];  // odd one out, pass through
        end
    end
    
    // Stage 3: Add pairs from stage 2
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 4; i = i + 1)
                stage3[i] <= 16'd0;
        end else begin
            stage3[0] <= stage2[0] + stage2[1];
            stage3[1] <= stage2[2] + stage2[3];
            stage3[2] <= stage2[4] + stage2[5];
            stage3[3] <= stage2[6];  // pass through
        end
    end
    
    // Stage 4: Add pairs from stage 3
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            stage4[0] <= 16'd0;
            stage4[1] <= 16'd0;
        end else begin
            stage4[0] <= stage3[0] + stage3[1];
            stage4[1] <= stage3[2] + stage3[3];
        end
    end
    
    // Stage 5: Final addition
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            stage5 <= 16'd0;
        else
            stage5 <= stage4[0] + stage4[1];
    end
    
    // Output register
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            y <= 16'd0;
        else
            y <= stage5;
    end

endmodule