module apifast__firr18__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Delay line (tap 0 = newest sample)
    reg [7:0] delay [0:17];
    integer i;

    // Pipeline stages for sum tree
    reg [15:0] sum_stage1 [0:8];  // 9 pairs from 18 taps
    reg [15:0] sum_stage2 [0:4];  // 5 sums from stage1 (9 inputs -> 4 pairs + 1)
    reg [15:0] sum_stage3 [0:2];  // 3 sums from stage2 (5 inputs -> 2 pairs + 1)
    reg [15:0] sum_stage4 [0:1];  // 2 sums from stage3 (3 inputs -> 1 pair + 1)
    reg [15:0] sum_stage5;        // final sum

    // Shift delay line and load new sample
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 18; i = i + 1)
                delay[i] <= 8'd0;
        end else begin
            // Shift: tap[0] gets new x, others shift right
            for (i = 17; i > 0; i = i - 1)
                delay[i] <= delay[i-1];
            delay[0] <= x;
        end
    end

    // Stage 1: Multiply each tap by (k+1) and sum in pairs
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 9; i = i + 1)
                sum_stage1[i] <= 16'd0;
        end else begin
            sum_stage1[0] <= (delay[0] * 1)  + (delay[1] * 2);
            sum_stage1[1] <= (delay[2] * 3)  + (delay[3] * 4);
            sum_stage1[2] <= (delay[4] * 5)  + (delay[5] * 6);
            sum_stage1[3] <= (delay[6] * 7)  + (delay[7] * 8);
            sum_stage1[4] <= (delay[8] * 9)  + (delay[9] * 10);
            sum_stage1[5] <= (delay[10] * 11) + (delay[11] * 12);
            sum_stage1[6] <= (delay[12] * 13) + (delay[13] * 14);
            sum_stage1[7] <= (delay[14] * 15) + (delay[15] * 16);
            sum_stage1[8] <= (delay[16] * 17) + (delay[17] * 18);
        end
    end

    // Stage 2: Pairwise sum of stage1 results
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 5; i = i + 1)
                sum_stage2[i] <= 16'd0;
        end else begin
            sum_stage2[0] <= sum_stage1[0] + sum_stage1[1];
            sum_stage2[1] <= sum_stage1[2] + sum_stage1[3];
            sum_stage2[2] <= sum_stage1[4] + sum_stage1[5];
            sum_stage2[3] <= sum_stage1[6] + sum_stage1[7];
            sum_stage2[4] <= sum_stage1[8];  // odd one
        end
    end

    // Stage 3: Pairwise sum of stage2 results
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 3; i = i + 1)
                sum_stage3[i] <= 16'd0;
        end else begin
            sum_stage3[0] <= sum_stage2[0] + sum_stage2[1];
            sum_stage3[1] <= sum_stage2[2] + sum_stage2[3];
            sum_stage3[2] <= sum_stage2[4];  // odd one
        end
    end

    // Stage 4: Pairwise sum of stage3 results
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sum_stage4[0] <= 16'd0;
            sum_stage4[1] <= 16'd0;
        end else begin
            sum_stage4[0] <= sum_stage3[0] + sum_stage3[1];
            sum_stage4[1] <= sum_stage3[2];  // odd one
        end
    end

    // Stage 5: Final sum
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            sum_stage5 <= 16'd0;
        else
            sum_stage5 <= sum_stage4[0] + sum_stage4[1];
    end

    // Output register (registered y)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            y <= 16'd0;
        else
            y <= sum_stage5;
    end

endmodule