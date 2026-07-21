module apifast__firr18__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Internal delay line of 18 samples (tap 0 = newest)
    reg [7:0] delay_line [17:0];
    integer k;

    // Pipeline stages for sum computation
    // Stage 1: multiply each tap by coefficient (k+1) and accumulate pairwise
    reg [15:0] stage1_sum [8:0]; // 9 sums from pairs (0-1,2-3,...,16-17)

    // Stage 2: accumulate 9 partial sums into 5 sums (8+1 extra)
    reg [15:0] stage2_sum [4:0]; // 5 sums

    // Stage 3: accumulate 5 sums into 3 sums
    reg [15:0] stage3_sum [2:0]; // 3 sums

    // Stage 4: accumulate 3 sums into 2 sums
    reg [15:0] stage4_sum [1:0]; // 2 sums

    // Stage 5: final sum to output
    reg [15:0] final_sum;

    // Delay line update and all pipeline registers
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear delay line
            for (k = 0; k < 18; k = k + 1)
                delay_line[k] <= 8'd0;

            // Clear all pipeline registers
            for (k = 0; k < 9; k = k + 1)
                stage1_sum[k] <= 16'd0;
            for (k = 0; k < 5; k = k + 1)
                stage2_sum[k] <= 16'd0;
            for (k = 0; k < 3; k = k + 1)
                stage3_sum[k] <= 16'd0;
            for (k = 0; k < 2; k = k + 1)
                stage4_sum[k] <= 16'd0;
            final_sum <= 16'd0;
            y <= 16'd0;
        end else begin
            // Shift delay line: oldest out, new x in at tap 0
            for (k = 17; k > 0; k = k - 1)
                delay_line[k] <= delay_line[k-1];
            delay_line[0] <= x;

            // Stage 1: multiply and pairwise sum
            // Coefficients: tap k has coefficient (k+1)
            // Each stage1_sum[i] gets sum of two adjacent tap*coeff products
            stage1_sum[0] <= (delay_line[0] * 1) + (delay_line[1] * 2);
            stage1_sum[1] <= (delay_line[2] * 3) + (delay_line[3] * 4);
            stage1_sum[2] <= (delay_line[4] * 5) + (delay_line[5] * 6);
            stage1_sum[3] <= (delay_line[6] * 7) + (delay_line[7] * 8);
            stage1_sum[4] <= (delay_line[8] * 9) + (delay_line[9] * 10);
            stage1_sum[5] <= (delay_line[10] * 11) + (delay_line[11] * 12);
            stage1_sum[6] <= (delay_line[12] * 13) + (delay_line[13] * 14);
            stage1_sum[7] <= (delay_line[14] * 15) + (delay_line[15] * 16);
            stage1_sum[8] <= (delay_line[16] * 17) + (delay_line[17] * 18);

            // Stage 2: sum pairs from stage1 (9 inputs -> 5 outputs)
            stage2_sum[0] <= stage1_sum[0] + stage1_sum[1];
            stage2_sum[1] <= stage1_sum[2] + stage1_sum[3];
            stage2_sum[2] <= stage1_sum[4] + stage1_sum[5];
            stage2_sum[3] <= stage1_sum[6] + stage1_sum[7];
            stage2_sum[4] <= stage1_sum[8]; // leftover

            // Stage 3: sum pairs from stage2 (5 inputs -> 3 outputs)
            stage3_sum[0] <= stage2_sum[0] + stage2_sum[1];
            stage3_sum[1] <= stage2_sum[2] + stage2_sum[3];
            stage3_sum[2] <= stage2_sum[4]; // leftover

            // Stage 4: sum pairs from stage3 (3 inputs -> 2 outputs)
            stage4_sum[0] <= stage3_sum[0] + stage3_sum[1];
            stage4_sum[1] <= stage3_sum[2]; // leftover

            // Stage 5: final sum
            final_sum <= stage4_sum[0] + stage4_sum[1];

            // Output registered
            y <= final_sum;
        end
    end

endmodule