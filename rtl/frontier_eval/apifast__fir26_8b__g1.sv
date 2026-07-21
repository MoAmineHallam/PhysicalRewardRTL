module apifast__fir26_8b__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Delay line for sample inputs
    reg [7:0] delay_line [0:25];
    
    // Pipeline registers for each tap product
    reg [23:0] tap_prod [0:25];  // 8-bit * 16-bit = 24-bit max
    
    // First pipeline stage: shift delay line and compute products
    always @(posedge clk or negedge rst_n) begin
        integer i;
        if (!rst_n) begin
            for (i = 0; i < 26; i = i + 1) begin
                delay_line[i] <= 8'd0;
                tap_prod[i] <= 24'd0;
            end
        end else begin
            // Shift delay line
            delay_line[0] <= x;
            for (i = 1; i < 26; i = i + 1) begin
                delay_line[i] <= delay_line[i-1];
            end
            
            // Compute products (each coefficient can be represented as a sum of shifts)
            // Coefficients: [3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25, 27, 27, 25, 23, 21, 19, 17, 15, 13, 11, 9, 7, 5, 3]
            // 3 = 2+1, 5 = 4+1, 7 = 8-1, 9 = 8+1, 11 = 8+2+1, 13 = 8+4+1, 15 = 16-1
            // 17 = 16+1, 19 = 16+2+1, 21 = 16+4+1, 23 = 16+8-1, 25 = 16+8+1, 27 = 16+8+2+1
            
            // Tap 0: coeff=3 = 2+1
            tap_prod[0] <= {delay_line[0], 1'b0} + delay_line[0]; // *3
            
            // Tap 1: coeff=5 = 4+1
            tap_prod[1] <= {delay_line[1], 2'b00} + delay_line[1]; // *5
            
            // Tap 2: coeff=7 = 8-1
            tap_prod[2] <= {delay_line[2], 3'b000} - delay_line[2]; // *7
            
            // Tap 3: coeff=9 = 8+1
            tap_prod[3] <= {delay_line[3], 3'b000} + delay_line[3]; // *9
            
            // Tap 4: coeff=11 = 8+2+1
            tap_prod[4] <= {delay_line[4], 3'b000} + {delay_line[4], 1'b0} + delay_line[4]; // *11
            
            // Tap 5: coeff=13 = 8+4+1
            tap_prod[5] <= {delay_line[5], 3'b000} + {delay_line[5], 2'b00} + delay_line[5]; // *13
            
            // Tap 6: coeff=15 = 16-1
            tap_prod[6] <= {delay_line[6], 4'b0000} - delay_line[6]; // *15
            
            // Tap 7: coeff=17 = 16+1
            tap_prod[7] <= {delay_line[7], 4'b0000} + delay_line[7]; // *17
            
            // Tap 8: coeff=19 = 16+2+1
            tap_prod[8] <= {delay_line[8], 4'b0000} + {delay_line[8], 1'b0} + delay_line[8]; // *19
            
            // Tap 9: coeff=21 = 16+4+1
            tap_prod[9] <= {delay_line[9], 4'b0000} + {delay_line[9], 2'b00} + delay_line[9]; // *21
            
            // Tap 10: coeff=23 = 16+8-1
            tap_prod[10] <= {delay_line[10], 4'b0000} + {delay_line[10], 3'b000} - delay_line[10]; // *23
            
            // Tap 11: coeff=25 = 16+8+1
            tap_prod[11] <= {delay_line[11], 4'b0000} + {delay_line[11], 3'b000} + delay_line[11]; // *25
            
            // Tap 12: coeff=27 = 16+8+2+1
            tap_prod[12] <= {delay_line[12], 4'b0000} + {delay_line[12], 3'b000} + {delay_line[12], 1'b0} + delay_line[12]; // *27
            
            // Taps 13-25: symmetric coefficients (mirrored)
            tap_prod[13] <= {delay_line[13], 4'b0000} + {delay_line[13], 3'b000} + {delay_line[13], 1'b0} + delay_line[13]; // *27
            tap_prod[14] <= {delay_line[14], 4'b0000} + {delay_line[14], 3'b000} + delay_line[14]; // *25
            tap_prod[15] <= {delay_line[15], 4'b0000} + {delay_line[15], 3'b000} - delay_line[15]; // *23
            tap_prod[16] <= {delay_line[16], 4'b0000} + {delay_line[16], 2'b00} + delay_line[16]; // *21
            tap_prod[17] <= {delay_line[17], 4'b0000} + {delay_line[17], 1'b0} + delay_line[17]; // *19
            tap_prod[18] <= {delay_line[18], 4'b0000} + delay_line[18]; // *17
            tap_prod[19] <= {delay_line[19], 4'b0000} - delay_line[19]; // *15
            tap_prod[20] <= {delay_line[20], 3'b000} + {delay_line[20], 2'b00} + delay_line[20]; // *13
            tap_prod[21] <= {delay_line[21], 3'b000} + {delay_line[21], 1'b0} + delay_line[21]; // *11
            tap_prod[22] <= {delay_line[22], 3'b000} + delay_line[22]; // *9
            tap_prod[23] <= {delay_line[23], 3'b000} - delay_line[23]; // *7
            tap_prod[24] <= {delay_line[24], 2'b00} + delay_line[24]; // *5
            tap_prod[25] <= {delay_line[25], 1'b0} + delay_line[25]; // *3
        end
    end
    
    // Second pipeline stage: pairwise addition tree (logarithmic)
    reg [27:0] sum_stage1 [0:12]; // 26 inputs -> 13 pairs
    
    always @(posedge clk or negedge rst_n) begin
        integer i;
        if (!rst_n) begin
            for (i = 0; i < 13; i = i + 1) begin
                sum_stage1[i] <= 28'd0;
            end
        end else begin
            // Add pairs
            for (i = 0; i < 13; i = i + 1) begin
                sum_stage1[i] <= tap_prod[2*i] + tap_prod[2*i + 1];
            end
        end
    end
    
    // Third pipeline stage: 13 -> 7 pairs (one group of 3)
    reg [28:0] sum_stage2 [0:6];
    
    always @(posedge clk or negedge rst_n) begin
        integer i;
        if (!rst_n) begin
            for (i = 0; i < 7; i = i + 1) begin
                sum_stage2[i] <= 29'd0;
            end
        end else begin
            // First 6 groups: pairs
            for (i = 0; i < 6; i = i + 1) begin
                sum_stage2[i] <= sum_stage1[2*i] + sum_stage1[2*i + 1];
            end
            // Last group: single remaining element
            sum_stage2[6] <= sum_stage1[12];
        end
    end
    
    // Fourth pipeline stage: 7 -> 4 pairs
    reg [29:0] sum_stage3 [0:3];
    
    always @(posedge clk or negedge rst_n) begin
        integer i;
        if (!rst_n) begin
            for (i = 0; i < 4; i = i + 1) begin
                sum_stage3[i] <= 30'd0;
            end
        end else begin
            for (i = 0; i < 3; i = i + 1) begin
                sum_stage3[i] <= sum_stage2[2*i] + sum_stage2[2*i + 1];
            end
            sum_stage3[3] <= sum_stage2[6];
        end
    end
    
    // Fifth pipeline stage: 4 -> 2 pairs
    reg [30:0] sum_stage4 [0:1];
    
    always @(posedge clk or negedge rst_n) begin
        integer i;
        if (!rst_n) begin
            for (i = 0; i < 2; i = i + 1) begin
                sum_stage4[i] <= 31'd0;
            end
        end else begin
            for (i = 0; i < 2; i = i + 1) begin
                sum_stage4[i] <= sum_stage3[2*i] + sum_stage3[2*i + 1];
            end
        end
    end
    
    // Sixth pipeline stage: 2 -> 1 final sum and output
    reg [31:0] final_sum;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            final_sum <= 32'd0;
            y <= 16'd0;
        end else begin
            final_sum <= sum_stage4[0] + sum_stage4[1];
            y <= final_sum[15:0];  // Take low 16 bits
        end
    end

endmodule