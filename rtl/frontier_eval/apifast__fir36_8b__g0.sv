module apifast__fir36_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Delay line registers (pipeline stage 0)
    reg [7:0] delay [0:35];
    integer i;
    
    // First stage multipliers for first 18 taps (left half)
    reg [15:0] prod_left [0:17];  // product width: 8*8=16 bits
    // First stage multipliers for last 18 taps (right half)
    reg [15:0] prod_right [0:17];
    
    // Intermediate sum stages (pipeline)
    reg [15:0] sum_l1 [0:8];  // level 1 partial sums (left half)
    reg [15:0] sum_r1 [0:8];  // level 1 partial sums (right half)
    
    reg [15:0] sum_l2 [0:4];
    reg [15:0] sum_r2 [0:4];
    
    reg [15:0] sum_l3 [0:2];
    reg [15:0] sum_r3 [0:2];
    
    reg [15:0] sum_l4 [0:1];
    reg [15:0] sum_r4 [0:1];
    
    reg [15:0] sum_l5;
    reg [15:0] sum_r5;
    
    reg [15:0] total_sum;
    
    // Coefficients
    function [7:0] coeff;
        input integer index;
        begin
            case(index)
                0:  coeff = 8'd3;
                1:  coeff = 8'd5;
                2:  coeff = 8'd7;
                3:  coeff = 8'd9;
                4:  coeff = 8'd11;
                5:  coeff = 8'd13;
                6:  coeff = 8'd15;
                7:  coeff = 8'd17;
                8:  coeff = 8'd19;
                9:  coeff = 8'd21;
                10: coeff = 8'd23;
                11: coeff = 8'd25;
                12: coeff = 8'd27;
                13: coeff = 8'd29;
                14: coeff = 8'd31;
                15: coeff = 8'd33;
                16: coeff = 8'd35;
                17: coeff = 8'd37;
                18: coeff = 8'd37;
                19: coeff = 8'd35;
                20: coeff = 8'd33;
                21: coeff = 8'd31;
                22: coeff = 8'd29;
                23: coeff = 8'd27;
                24: coeff = 8'd25;
                25: coeff = 8'd23;
                26: coeff = 8'd21;
                27: coeff = 8'd19;
                28: coeff = 8'd17;
                29: coeff = 8'd15;
                30: coeff = 8'd13;
                31: coeff = 8'd11;
                32: coeff = 8'd9;
                33: coeff = 8'd7;
                34: coeff = 8'd5;
                35: coeff = 8'd3;
            endcase
        end
    endfunction
    
    // All sequential logic
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear all registers
            for (i = 0; i < 36; i = i + 1) begin
                delay[i] <= 8'd0;
            end
            
            for (i = 0; i < 18; i = i + 1) begin
                prod_left[i] <= 16'd0;
                prod_right[i] <= 16'd0;
            end
            
            for (i = 0; i < 9; i = i + 1) begin
                sum_l1[i] <= 16'd0;
                sum_r1[i] <= 16'd0;
            end
            
            for (i = 0; i < 5; i = i + 1) begin
                sum_l2[i] <= 16'd0;
                sum_r2[i] <= 16'd0;
            end
            
            for (i = 0; i < 3; i = i + 1) begin
                sum_l3[i] <= 16'd0;
                sum_r3[i] <= 16'd0;
            end
            
            for (i = 0; i < 2; i = i + 1) begin
                sum_l4[i] <= 16'd0;
                sum_r4[i] <= 16'd0;
            end
            
            sum_l5 <= 16'd0;
            sum_r5 <= 16'd0;
            total_sum <= 16'd0;
            y <= 16'd0;
            
        end else begin
            // Stage 0: Shift delay line and load new sample
            for (i = 35; i > 0; i = i - 1) begin
                delay[i] <= delay[i-1];
            end
            delay[0] <= x;
            
            // Stage 1: Multiply (left half: taps 0-17, right half: taps 18-35)
            for (i = 0; i < 18; i = i + 1) begin
                prod_left[i] <= delay[i] * coeff(i);
                prod_right[i] <= delay[35-i] * coeff(35-i);
            end
            
            // Stage 2: Pairwise sums - level 1 (9 pairs each side)
            for (i = 0; i < 9; i = i + 1) begin
                sum_l1[i] <= prod_left[2*i] + prod_left[2*i+1];
                sum_r1[i] <= prod_right[2*i] + prod_right[2*i+1];
            end
            
            // Stage 3: Pairwise sums - level 2 (5 sums: 4 pairs + 1 remainder)
            for (i = 0; i < 4; i = i + 1) begin
                sum_l2[i] <= sum_l1[2*i] + sum_l1[2*i+1];
                sum_r2[i] <= sum_r1[2*i] + sum_r1[2*i+1];
            end
            sum_l2[4] <= sum_l1[8];
            sum_r2[4] <= sum_r1[8];
            
            // Stage 4: Pairwise sums - level 3 (3 sums)
            for (i = 0; i < 2; i = i + 1) begin
                sum_l3[i] <= sum_l2[2*i] + sum_l2[2*i+1];
                sum_r3[i] <= sum_r2[2*i] + sum_r2[2*i+1];
            end
            sum_l3[2] <= sum_l2[4];
            sum_r3[2] <= sum_r2[4];
            
            // Stage 5: Pairwise sums - level 4 (2 sums)
            sum_l4[0] <= sum_l3[0] + sum_l3[1];
            sum_l4[1] <= sum_l3[2];
            sum_r4[0] <= sum_r3[0] + sum_r3[1];
            sum_r4[1] <= sum_r3[2];
            
            // Stage 6: Final sums for each half
            sum_l5 <= sum_l4[0] + sum_l4[1];
            sum_r5 <= sum_r4[0] + sum_r4[1];
            
            // Stage 7: Combine halves
            total_sum <= sum_l5 + sum_r5;
            
            // Stage 8: Output register (low 16 bits)
            y <= total_sum;
        end
    end
    
endmodule