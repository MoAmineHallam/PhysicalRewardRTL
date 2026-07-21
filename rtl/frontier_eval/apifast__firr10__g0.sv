module apifast__firr10__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // 10-element delay line (tap 0 = newest)
    reg [7:0] tap [0:9];
    
    // Pipeline registers for multiplication results (stage 1)
    reg [15:0] mult_stage1 [0:9];  // (k+1) * tap[k] up to 16 bits
    
    // Pipeline registers for adder tree (stages 2-5)
    reg [15:0] sum_stage2 [0:4];  // 5 pairs
    reg [15:0] sum_stage3 [0:2];  // 3 pairs (2 + 1 remaining)
    reg [15:0] sum_stage4 [0:1];  // 2 pairs
    reg [15:0] sum_stage5;        // final sum
    
    integer k;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear all delay line taps
            for (k = 0; k < 10; k = k + 1) begin
                tap[k] <= 8'd0;
            end
            
            // Clear all pipeline stages
            for (k = 0; k < 10; k = k + 1) begin
                mult_stage1[k] <= 16'd0;
            end
            
            for (k = 0; k < 5; k = k + 1) begin
                sum_stage2[k] <= 16'd0;
            end
            
            for (k = 0; k < 3; k = k + 1) begin
                sum_stage3[k] <= 16'd0;
            end
            
            for (k = 0; k < 2; k = k + 1) begin
                sum_stage4[k] <= 16'd0;
            end
            
            sum_stage5 <= 16'd0;
            y <= 16'd0;
            
        end else begin
            // Shift delay line and insert new sample
            tap[9] <= tap[8];
            tap[8] <= tap[7];
            tap[7] <= tap[6];
            tap[6] <= tap[5];
            tap[5] <= tap[4];
            tap[4] <= tap[3];
            tap[3] <= tap[2];
            tap[2] <= tap[1];
            tap[1] <= tap[0];
            tap[0] <= x;
            
            // Stage 1: Multiply each tap by its coefficient (k+1)
            // Coefficients: 1,2,3,4,5,6,7,8,9,10
            mult_stage1[0] <= {8'd0, tap[0]} * 16'd1;    // 1 * tap[0]
            mult_stage1[1] <= {8'd0, tap[1]} * 16'd2;    // 2 * tap[1]
            mult_stage1[2] <= {8'd0, tap[2]} * 16'd3;    // 3 * tap[2]
            mult_stage1[3] <= {8'd0, tap[3]} * 16'd4;    // 4 * tap[3]
            mult_stage1[4] <= {8'd0, tap[4]} * 16'd5;    // 5 * tap[4]
            mult_stage1[5] <= {8'd0, tap[5]} * 16'd6;    // 6 * tap[5]
            mult_stage1[6] <= {8'd0, tap[6]} * 16'd7;    // 7 * tap[6]
            mult_stage1[7] <= {8'd0, tap[7]} * 16'd8;    // 8 * tap[7]
            mult_stage1[8] <= {8'd0, tap[8]} * 16'd9;    // 9 * tap[8]
            mult_stage1[9] <= {8'd0, tap[9]} * 16'd10;   // 10 * tap[9]
            
            // Stage 2: Sum pairs (5 additions)
            sum_stage2[0] <= mult_stage1[0] + mult_stage1[1];
            sum_stage2[1] <= mult_stage1[2] + mult_stage1[3];
            sum_stage2[2] <= mult_stage1[4] + mult_stage1[5];
            sum_stage2[3] <= mult_stage1[6] + mult_stage1[7];
            sum_stage2[4] <= mult_stage1[8] + mult_stage1[9];
            
            // Stage 3: Sum pairs from stage 2 (2 additions + 1 pass-through)
            sum_stage3[0] <= sum_stage2[0] + sum_stage2[1];
            sum_stage3[1] <= sum_stage2[2] + sum_stage2[3];
            sum_stage3[2] <= sum_stage2[4];
            
            // Stage 4: Final pair sums
            sum_stage4[0] <= sum_stage3[0] + sum_stage3[1];
            sum_stage4[1] <= sum_stage3[2];
            
            // Stage 5: Final addition and output
            sum_stage5 <= sum_stage4[0] + sum_stage4[1];
            y <= sum_stage5;
        end
    end

endmodule