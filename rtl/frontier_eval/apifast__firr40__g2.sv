module apifast__firr40__g2 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Delay line: 40 taps, each 8 bits
    reg [7:0] tap [0:39];
    integer k;
    
    // Pipeline stages for sum reduction
    // Stage 0: multiply and first add (for pairs)
    reg [23:0] stage0_partial [0:19]; // 20 results from pairs
    // Stage 1: sum pairs from stage0 -> 10 results
    reg [24:0] stage1_partial [0:9];
    // Stage 2: sum pairs from stage1 -> 5 results
    reg [25:0] stage2_partial [0:4];
    // Stage 3: sum pairs from stage2 -> 3 results (5/2 = 2 pairs + 1 leftover)
    reg [26:0] stage3_partial [0:2];
    // Stage 4: sum pairs from stage3 -> 2 results
    reg [27:0] stage4_partial [0:1];
    // Stage 5: final sum
    reg [28:0] stage5_result;

    // Update delay line and compute all products (combinational)
    wire [15:0] product [0:39];
    generate
        genvar i;
        for (i = 0; i < 40; i = i + 1) begin
            assign product[i] = (i+1) * tap[i];
        end
    endgenerate

    // Sequential logic
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear delay line
            for (k = 0; k < 40; k = k + 1)
                tap[k] <= 8'd0;
            
            // Clear pipeline stages
            for (k = 0; k < 20; k = k + 1)
                stage0_partial[k] <= 24'd0;
            for (k = 0; k < 10; k = k + 1)
                stage1_partial[k] <= 25'd0;
            for (k = 0; k < 5; k = k + 1)
                stage2_partial[k] <= 26'd0;
            for (k = 0; k < 3; k = k + 1)
                stage3_partial[k] <= 27'd0;
            for (k = 0; k < 2; k = k + 1)
                stage4_partial[k] <= 28'd0;
            stage5_result <= 29'd0;
            
            y <= 16'd0;
        end
        else begin
            // Shift delay line and insert new sample
            for (k = 39; k > 0; k = k - 1)
                tap[k] <= tap[k-1];
            tap[0] <= x;
            
            // Stage 0: pair adjacent products (40 -> 20)
            for (k = 0; k < 20; k = k + 1)
                stage0_partial[k] <= product[2*k] + product[2*k+1];
            
            // Stage 1: sum pairs from stage0 (20 -> 10)
            for (k = 0; k < 10; k = k + 1)
                stage1_partial[k] <= stage0_partial[2*k] + stage0_partial[2*k+1];
            
            // Stage 2: sum pairs from stage1 (10 -> 5)
            for (k = 0; k < 5; k = k + 1)
                stage2_partial[k] <= stage1_partial[2*k] + stage1_partial[2*k+1];
            
            // Stage 3: sum pairs from stage2 (5 -> 3)
            stage3_partial[0] <= stage2_partial[0] + stage2_partial[1];
            stage3_partial[1] <= stage2_partial[2] + stage2_partial[3];
            stage3_partial[2] <= {1'b0, stage2_partial[4]}; // leftover, zero-extend
            
            // Stage 4: sum pairs from stage3 (3 -> 2)
            stage4_partial[0] <= stage3_partial[0] + stage3_partial[1];
            stage4_partial[1] <= {1'b0, stage3_partial[2]}; // leftover, zero-extend
            
            // Stage 5: final sum
            stage5_result <= stage4_partial[0] + stage4_partial[1];
            
            // Output: low 16 bits of final sum
            y <= stage5_result[15:0];
        end
    end

endmodule