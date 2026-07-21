module apifast__firr18__g5 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Delay line for 18 samples (tap 0 = newest)
    reg [7:0] delay_line [17:0];
    
    // Pipeline stages for partial sums
    // Stage 0: products from taps 0-17
    // Stage 1-4: reduction tree additions
    
    // First stage pipeline registers for products
    reg [15:0] prod [17:0];
    
    // Pipeline for reduction tree
    reg [15:0] sum_stage1 [8:0];  // 9 sums of pairs
    reg [15:0] sum_stage2 [4:0];  // 5 sums of pairs (one from stage1)
    reg [15:0] sum_stage3 [2:0];  // 3 sums
    reg [15:0] sum_stage4 [1:0];  // 2 sums
    reg [15:0] sum_stage5;       // final sum
    
    integer i;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear all delay line
            for (i = 0; i < 18; i = i + 1) begin
                delay_line[i] <= 8'd0;
            end
            
            // Clear all pipeline registers
            for (i = 0; i < 18; i = i + 1) begin
                prod[i] <= 16'd0;
            end
            for (i = 0; i < 9; i = i + 1) begin
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
            // Update delay line: shift and insert new sample
            delay_line[0] <= x;
            for (i = 1; i < 18; i = i + 1) begin
                delay_line[i] <= delay_line[i-1];
            end
            
            // Pipeline Stage 0: Multiply each tap with coefficient (k+1)
            // Coefficient for tap k is (k+1)
            prod[0] <= {8'd0, delay_line[0]} * 18'd1;      // tap 0 * 1
            prod[1] <= {8'd0, delay_line[1]} * 18'd2;      // tap 1 * 2
            prod[2] <= {8'd0, delay_line[2]} * 18'd3;      // tap 2 * 3
            prod[3] <= {8'd0, delay_line[3]} * 18'd4;      // tap 3 * 4
            prod[4] <= {8'd0, delay_line[4]} * 18'd5;      // tap 4 * 5
            prod[5] <= {8'd0, delay_line[5]} * 18'd6;      // tap 5 * 6
            prod[6] <= {8'd0, delay_line[6]} * 18'd7;      // tap 6 * 7
            prod[7] <= {8'd0, delay_line[7]} * 18'd8;      // tap 7 * 8
            prod[8] <= {8'd0, delay_line[8]} * 18'd9;      // tap 8 * 9
            prod[9] <= {8'd0, delay_line[9]} * 18'd10;     // tap 9 * 10
            prod[10] <= {8'd0, delay_line[10]} * 18'd11;   // tap 10 * 11
            prod[11] <= {8'd0, delay_line[11]} * 18'd12;   // tap 11 * 12
            prod[12] <= {8'd0, delay_line[12]} * 18'd13;   // tap 12 * 13
            prod[13] <= {8'd0, delay_line[13]} * 18'd14;   // tap 13 * 14
            prod[14] <= {8'd0, delay_line[14]} * 18'd15;   // tap 14 * 15
            prod[15] <= {8'd0, delay_line[15]} * 18'd16;   // tap 15 * 16
            prod[16] <= {8'd0, delay_line[16]} * 18'd17;   // tap 16 * 17
            prod[17] <= {8'd0, delay_line[17]} * 18'd18;   // tap 17 * 18
            
            // Pipeline Stage 1: Sum pairs of products
            sum_stage1[0] <= prod[0] + prod[1];
            sum_stage1[1] <= prod[2] + prod[3];
            sum_stage1[2] <= prod[4] + prod[5];
            sum_stage1[3] <= prod[6] + prod[7];
            sum_stage1[4] <= prod[8] + prod[9];
            sum_stage1[5] <= prod[10] + prod[11];
            sum_stage1[6] <= prod[12] + prod[13];
            sum_stage1[7] <= prod[14] + prod[15];
            sum_stage1[8] <= prod[16] + prod[17];
            
            // Pipeline Stage 2: Sum pairs from stage 1
            sum_stage2[0] <= sum_stage1[0] + sum_stage1[1];
            sum_stage2[1] <= sum_stage1[2] + sum_stage1[3];
            sum_stage2[2] <= sum_stage1[4] + sum_stage1[5];
            sum_stage2[3] <= sum_stage1[6] + sum_stage1[7];
            sum_stage2[4] <= sum_stage1[8];  // pass through odd one
            
            // Pipeline Stage 3: Sum pairs from stage 2
            sum_stage3[0] <= sum_stage2[0] + sum_stage2[1];
            sum_stage3[1] <= sum_stage2[2] + sum_stage2[3];
            sum_stage3[2] <= sum_stage2[4];  // pass through odd one
            
            // Pipeline Stage 4: Final pair sums
            sum_stage4[0] <= sum_stage3[0] + sum_stage3[1];
            sum_stage4[1] <= sum_stage3[2];  // pass through
            
            // Pipeline Stage 5: Final sum
            sum_stage5 <= sum_stage4[0] + sum_stage4[1];
            
            // Output registered
            y <= sum_stage5[15:0];
        end
    end

endmodule