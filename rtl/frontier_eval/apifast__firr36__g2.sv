module apifast__firr36__g2 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Delay line: 36 taps of 8-bit unsigned samples
    reg [7:0] tap [0:35];
    integer i;
    
    // Pipeline registers for partial sums
    // Stage 1: multiply-accumulate for pairs (or individual for odd count)
    reg [15:0] sum_stage1 [0:17]; // 18 partial sums
    
    // Stage 2: sum of adjacent pairs from stage1
    reg [15:0] sum_stage2 [0:8];  // 9 partial sums
    
    // Stage 3: sum of adjacent pairs from stage2
    reg [15:0] sum_stage3 [0:4];  // 5 partial sums
    
    // Stage 4: sum of adjacent pairs from stage3
    reg [15:0] sum_stage4 [0:2];  // 3 partial sums
    
    // Stage 5: sum of adjacent pairs from stage4
    reg [15:0] sum_stage5 [0:1];  // 2 partial sums
    
    // Stage 6: final sum
    reg [15:0] final_sum;

    // Shift register for delay line (update on clock edge)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 36; i = i + 1)
                tap[i] <= 8'd0;
        end else begin
            // Shift right: tap[0] gets new sample, others shift
            tap[0] <= x;
            for (i = 1; i < 36; i = i + 1)
                tap[i] <= tap[i-1];
        end
    end

    // Stage 1: Multiply coefficients (k+1) with taps, sum in pairs
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 18; i = i + 1)
                sum_stage1[i] <= 16'd0;
        end else begin
            // Pair taps 0-1, 2-3, ... 34-35
            // Coefficient for tap k = k+1
            // For each pair (2k, 2k+1): (2k+1)*tap[2k] + (2k+2)*tap[2k+1]
            for (i = 0; i < 18; i = i + 1) begin
                sum_stage1[i] <= ({1'b0, tap[2*i]} * (2*i+1)) 
                               + ({1'b0, tap[2*i+1]} * (2*i+2));
            end
        end
    end

    // Stage 2: Sum adjacent pairs from stage1
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 9; i = i + 1)
                sum_stage2[i] <= 16'd0;
        end else begin
            for (i = 0; i < 9; i = i + 1)
                sum_stage2[i] <= sum_stage1[2*i] + sum_stage1[2*i+1];
        end
    end

    // Stage 3: Sum adjacent pairs from stage2
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 5; i = i + 1)
                sum_stage3[i] <= 16'd0;
        end else begin
            for (i = 0; i < 4; i = i + 1)
                sum_stage3[i] <= sum_stage2[2*i] + sum_stage2[2*i+1];
            // Last element gets sum_stage2[8] (odd one out)
            sum_stage3[4] <= sum_stage2[8];
        end
    end

    // Stage 4: Sum adjacent pairs from stage3
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 3; i = i + 1)
                sum_stage4[i] <= 16'd0;
        end else begin
            sum_stage4[0] <= sum_stage3[0] + sum_stage3[1];
            sum_stage4[1] <= sum_stage3[2] + sum_stage3[3];
            sum_stage4[2] <= sum_stage3[4]; // odd one out
        end
    end

    // Stage 5: Sum adjacent pairs from stage4
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sum_stage5[0] <= 16'd0;
            sum_stage5[1] <= 16'd0;
        end else begin
            sum_stage5[0] <= sum_stage4[0] + sum_stage4[1];
            sum_stage5[1] <= sum_stage4[2];
        end
    end

    // Stage 6: Final sum and output register
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            final_sum <= 16'd0;
            y <= 16'd0;
        end else begin
            final_sum <= sum_stage5[0] + sum_stage5[1];
            y <= final_sum;
        end
    end

endmodule