module apifast__firr40__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

// Delay line registers (tap 0 = newest = current x)
reg [7:0] delay [0:39];

// Pipeline registers for partial sums
reg [15:0] sum_stage0 [0:19];  // First stage: 20 multiply-accumulate pairs
reg [15:0] sum_stage1 [0:9];   // Second stage: 10 additions
reg [15:0] sum_stage2 [0:4];   // Third stage: 5 additions
reg [15:0] sum_stage3 [0:2];   // Fourth stage: 3 additions
reg [15:0] sum_stage4 [0:1];   // Fifth stage: 2 additions
reg [15:0] sum_stage5;         // Final stage: 1 addition

integer i, j;

// Pipeline delay of 6 cycles from input to output
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        // Clear delay line
        for (i = 0; i < 40; i = i + 1) begin
            delay[i] <= 8'd0;
        end
        
        // Clear all pipeline stages
        for (i = 0; i < 20; i = i + 1) begin
            sum_stage0[i] <= 16'd0;
        end
        for (i = 0; i < 10; i = i + 1) begin
            sum_stage1[i] <= 16'd0;
        end
        for (i = 0; i < 5; i = i + 1) begin
            sum_stage2[i] <= 16'd0;
        end
        for (i = 0; i < 3; i = i + 1) begin
            sum_stage3[i] <= 16'd0;
        end
        for (i = 0; i < 2; i = i + 1) begin
            sum_stage4[i] <= 16'd0;
        end
        sum_stage5 <= 16'd0;
        y <= 16'd0;
    end
    else begin
        // Shift delay line and insert new sample
        for (i = 39; i > 0; i = i - 1) begin
            delay[i] <= delay[i-1];
        end
        delay[0] <= x;
        
        // Stage 0: Compute 20 pairs of multiply-accumulate
        for (i = 0; i < 20; i = i + 1) begin
            sum_stage0[i] <= (delay[i] * (i+1)) + (delay[i+20] * (i+21));
        end
        
        // Stage 1: Sum pairs
        for (i = 0; i < 10; i = i + 1) begin
            sum_stage1[i] <= sum_stage0[i*2] + sum_stage0[i*2+1];
        end
        
        // Stage 2: Sum pairs
        for (i = 0; i < 5; i = i + 1) begin
            sum_stage2[i] <= sum_stage1[i*2] + sum_stage1[i*2+1];
        end
        
        // Stage 3: Sum pairs (3 inputs: 2 from pairs + leftover)
        sum_stage3[0] <= sum_stage2[0] + sum_stage2[1];
        sum_stage3[1] <= sum_stage2[2] + sum_stage2[3];
        sum_stage3[2] <= sum_stage2[4];
        
        // Stage 4: Sum pairs (3 inputs)
        sum_stage4[0] <= sum_stage3[0] + sum_stage3[1];
        sum_stage4[1] <= sum_stage3[2];
        
        // Stage 5: Final sum
        sum_stage5 <= sum_stage4[0] + sum_stage4[1];
        
        // Output registered (low 16 bits)
        y <= sum_stage5;
    end
end

endmodule