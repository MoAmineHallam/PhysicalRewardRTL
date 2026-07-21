module apifast__firr26__g4 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Delay line: 26 registers for samples (tap 0 = newest)
    reg [7:0] delay_line [0:25];
    
    // Pipeline registers for multiplication results (stages 0-25)
    // Each stage accumulates the sum of products for a subset of taps
    // To minimize critical path: one multiply per stage, then pipeline add
    
    // First stage: multiply taps 0-12 (or split differently)
    // We'll do 26 multiplies in parallel, then tree-add with pipelining
    
    // Pipeline registers for products
    reg [15:0] prod [0:25];  // (k+1) * tap[k] fits in 16 bits max: 26*255 = 6630 < 65536
    
    // Tree adder pipeline stages (log2(26) = 5 stages needed for reduction)
    // Stage0: 26 -> 13 sums
    reg [15:0] sum_stage0 [0:12];
    // Stage1: 13 -> 7 sums (13/2 = 6 pairs + 1 leftover)
    reg [15:0] sum_stage1 [0:6];
    // Stage2: 7 -> 4 sums
    reg [15:0] sum_stage2 [0:3];
    // Stage3: 4 -> 2 sums
    reg [15:0] sum_stage3 [0:1];
    // Stage4: 2 -> 1 sum
    reg [15:0] sum_stage4;
    
    integer i;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear all delay line
            for (i = 0; i < 26; i = i + 1)
                delay_line[i] <= 8'd0;
            
            // Clear all product registers
            for (i = 0; i < 26; i = i + 1)
                prod[i] <= 16'd0;
            
            // Clear all sum pipeline stages
            for (i = 0; i < 13; i = i + 1)
                sum_stage0[i] <= 16'd0;
            for (i = 0; i < 7; i = i + 1)
                sum_stage1[i] <= 16'd0;
            for (i = 0; i < 4; i = i + 1)
                sum_stage2[i] <= 16'd0;
            for (i = 0; i < 2; i = i + 1)
                sum_stage3[i] <= 16'd0;
            sum_stage4 <= 16'd0;
            
            y <= 16'd0;
        end
        else begin
            // Shift delay line: tap0 gets current x, all others shift
            delay_line[0] <= x;
            for (i = 1; i < 26; i = i + 1)
                delay_line[i] <= delay_line[i-1];
            
            // Compute products (combinational in this stage, registered below)
            // Actually we register products here to pipeline them
            for (i = 0; i < 26; i = i + 1)
                prod[i] <= (i+1) * delay_line[i];  // (k+1) * tap[k]
            
            // Stage 0: sum pairs of products
            for (i = 0; i < 13; i = i + 1)
                sum_stage0[i] <= prod[2*i] + prod[2*i+1];
            // Note: 26 is even, so no leftover
            
            // Stage 1: sum pairs of stage0
            for (i = 0; i < 6; i = i + 1)
                sum_stage1[i] <= sum_stage0[2*i] + sum_stage0[2*i+1];
            sum_stage1[6] <= sum_stage0[12];  // leftover
            
            // Stage 2: sum pairs of stage1
            for (i = 0; i < 3; i = i + 1)
                sum_stage2[i] <= sum_stage1[2*i] + sum_stage1[2*i+1];
            sum_stage2[3] <= sum_stage1[6];  // leftover
            
            // Stage 3: sum pairs of stage2
            sum_stage3[0] <= sum_stage2[0] + sum_stage2[1];
            sum_stage3[1] <= sum_stage2[2] + sum_stage2[3];
            
            // Stage 4: final sum
            sum_stage4 <= sum_stage3[0] + sum_stage3[1];
            
            // Output: truncate to low 16 bits
            y <= sum_stage4[15:0];
        end
    end

endmodule