module apifast__fir40_8b__g2 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Delay line (40 samples, 8-bit unsigned)
    reg [7:0] delay [0:39];
    
    // Pipeline registers for products (40 taps × 16-bit products)
    reg [15:0] prod [0:39];
    
    // Adder tree pipeline stages
    reg [15:0] sum_stage1 [0:19];  // 20 sums
    reg [15:0] sum_stage2 [0:9];   // 10 sums
    reg [15:0] sum_stage3 [0:4];   // 5 sums
    reg [15:0] sum_stage4 [0:2];   // 3 sums
    reg [15:0] sum_stage5 [0:1];   // 2 sums
    reg [15:0] sum_stage6;         // 1 final sum

    // Coefficients (symmetric: 20 unique values mirrored)
    wire [7:0] coeff [0:39];
    assign coeff[0]  = 8'd3;
    assign coeff[1]  = 8'd5;
    assign coeff[2]  = 8'd7;
    assign coeff[3]  = 8'd9;
    assign coeff[4]  = 8'd11;
    assign coeff[5]  = 8'd13;
    assign coeff[6]  = 8'd15;
    assign coeff[7]  = 8'd17;
    assign coeff[8]  = 8'd19;
    assign coeff[9]  = 8'd21;
    assign coeff[10] = 8'd23;
    assign coeff[11] = 8'd25;
    assign coeff[12] = 8'd27;
    assign coeff[13] = 8'd29;
    assign coeff[14] = 8'd31;
    assign coeff[15] = 8'd33;
    assign coeff[16] = 8'd35;
    assign coeff[17] = 8'd37;
    assign coeff[18] = 8'd39;
    assign coeff[19] = 8'd41;
    assign coeff[20] = 8'd41;
    assign coeff[21] = 8'd39;
    assign coeff[22] = 8'd37;
    assign coeff[23] = 8'd35;
    assign coeff[24] = 8'd33;
    assign coeff[25] = 8'd31;
    assign coeff[26] = 8'd29;
    assign coeff[27] = 8'd27;
    assign coeff[28] = 8'd25;
    assign coeff[29] = 8'd23;
    assign coeff[30] = 8'd21;
    assign coeff[31] = 8'd19;
    assign coeff[32] = 8'd17;
    assign coeff[33] = 8'd15;
    assign coeff[34] = 8'd13;
    assign coeff[35] = 8'd11;
    assign coeff[36] = 8'd9;
    assign coeff[37] = 8'd7;
    assign coeff[38] = 8'd5;
    assign coeff[39] = 8'd3;

    integer i;
    integer j;

    // Sequential logic
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear delay line
            for (i = 0; i < 40; i = i + 1)
                delay[i] <= 8'd0;
            
            // Clear all pipeline registers
            for (i = 0; i < 40; i = i + 1)
                prod[i] <= 16'd0;
            for (i = 0; i < 20; i = i + 1)
                sum_stage1[i] <= 16'd0;
            for (i = 0; i < 10; i = i + 1)
                sum_stage2[i] <= 16'd0;
            for (i = 0; i < 5; i = i + 1)
                sum_stage3[i] <= 16'd0;
            for (i = 0; i < 3; i = i + 1)
                sum_stage4[i] <= 16'd0;
            for (i = 0; i < 2; i = i + 1)
                sum_stage5[i] <= 16'd0;
            sum_stage6 <= 16'd0;
            y <= 16'd0;
        end
        else begin
            // Shift delay line and insert new sample
            for (i = 39; i > 0; i = i - 1)
                delay[i] <= delay[i-1];
            delay[0] <= x;
            
            // Stage 0: multiply each delay by coefficient
            for (i = 0; i < 40; i = i + 1)
                prod[i] <= delay[i] * coeff[i];
            
            // Stage 1: sum pairs
            for (i = 0; i < 20; i = i + 1)
                sum_stage1[i] <= prod[2*i] + prod[2*i + 1];
            
            // Stage 2: sum pairs of stage1
            for (i = 0; i < 10; i = i + 1)
                sum_stage2[i] <= sum_stage1[2*i] + sum_stage1[2*i + 1];
            
            // Stage 3: sum pairs of stage2
            for (i = 0; i < 5; i = i + 1)
                sum_stage3[i] <= sum_stage2[2*i] + sum_stage2[2*i + 1];
            
            // Stage 4: sum pairs of stage3 (5 inputs -> 3 sums: 2 pairs + 1 leftover)
            sum_stage4[0] <= sum_stage3[0] + sum_stage3[1];
            sum_stage4[1] <= sum_stage3[2] + sum_stage3[3];
            sum_stage4[2] <= sum_stage3[4];  // leftover
            
            // Stage 5: sum pairs of stage4 (3 inputs -> 2 sums)
            sum_stage5[0] <= sum_stage4[0] + sum_stage4[1];
            sum_stage5[1] <= sum_stage4[2];  // leftover
            
            // Stage 6: final sum
            sum_stage6 <= sum_stage5[0] + sum_stage5[1];
            
            // Output registered (take low 16 bits)
            y <= sum_stage6;
        end
    end

endmodule