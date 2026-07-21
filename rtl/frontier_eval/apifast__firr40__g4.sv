module apifast__firr40__g4 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Delay line of past samples (tap 0 = newest)
    reg [7:0] taps [0:39];
    
    // Pipeline registers for partial sums
    // Stage 0: multiply and add for pairs
    reg [15:0] sum_stage0 [0:19]; // 20 partial sums
    
    // Stage 1: combine stage0 results
    reg [15:0] sum_stage1 [0:9];  // 10 partial sums
    
    // Stage 2: combine stage1 results
    reg [15:0] sum_stage2 [0:4];  // 5 partial sums
    
    // Stage 3: combine stage2 results
    reg [15:0] sum_stage3 [0:2];  // 3 partial sums
    
    // Stage 4: final combine
    reg [15:0] sum_stage4;        // 1 partial sum
    
    integer i, j;
    
    // Shift register and initial multiply-add
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 40; i = i + 1) begin
                taps[i] <= 8'd0;
            end
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
            sum_stage4 <= 16'd0;
            y <= 16'd0;
        end else begin
            // Shift delay line
            for (i = 39; i > 0; i = i - 1) begin
                taps[i] <= taps[i-1];
            end
            taps[0] <= x;
            
            // Stage 0: compute 20 pairs of (k+1)*tap[k] + (k+2)*tap[k+1]
            for (i = 0; i < 20; i = i + 1) begin
                sum_stage0[i] <= ( (i*2 + 1) * taps[i*2] ) + ( (i*2 + 2) * taps[i*2+1] );
            end
            
            // Stage 1: combine stage0 pairs
            for (i = 0; i < 10; i = i + 1) begin
                sum_stage1[i] <= sum_stage0[i*2] + sum_stage0[i*2+1];
            end
            
            // Stage 2: combine stage1 pairs
            for (i = 0; i < 5; i = i + 1) begin
                sum_stage2[i] <= sum_stage1[i*2] + sum_stage1[i*2+1];
            end
            
            // Stage 3: combine stage2 (5 values -> 3)
            sum_stage3[0] <= sum_stage2[0] + sum_stage2[1];
            sum_stage3[1] <= sum_stage2[2] + sum_stage2[3];
            sum_stage3[2] <= sum_stage2[4];  // unpaired
            
            // Stage 4: final combine
            sum_stage4 <= sum_stage3[0] + sum_stage3[1] + sum_stage3[2];
            
            // Output registered
            y <= sum_stage4;
        end
    end

endmodule