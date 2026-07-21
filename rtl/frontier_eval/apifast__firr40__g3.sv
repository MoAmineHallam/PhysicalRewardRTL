module apifast__firr40__g3 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // 40-element delay line (tap 0 = newest sample)
    reg [7:0] delay_line [0:39];
    
    // Pipeline registers for partial sums
    // Stage 0: multiply coefficient (k+1) with tap[k]
    // Stage 1-n: accumulate partial sums
    
    // First level of pipeline: multiply and accumulate in pairs/triples
    // We'll use a binary tree adder structure
    
    // Level 0: 40 products -> 20 sums
    reg [15:0] sum_l0 [0:19];
    // Level 1: 20 sums -> 10 sums
    reg [15:0] sum_l1 [0:9];
    // Level 2: 10 sums -> 5 sums
    reg [15:0] sum_l2 [0:4];
    // Level 3: 5 sums -> 3 sums (one group of 3, one of 2)
    reg [15:0] sum_l3 [0:2];
    // Level 4: 3 sums -> 2 sums
    reg [15:0] sum_l4 [0:1];
    // Final level: 2 sums -> 1 sum
    reg [15:0] sum_final;
    
    integer i;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear delay line
            for (i = 0; i < 40; i = i + 1)
                delay_line[i] <= 8'd0;
            
            // Clear all pipeline registers
            for (i = 0; i < 20; i = i + 1) sum_l0[i] <= 16'd0;
            for (i = 0; i < 10; i = i + 1) sum_l1[i] <= 16'd0;
            for (i = 0; i < 5;  i = i + 1) sum_l2[i] <= 16'd0;
            for (i = 0; i < 3;  i = i + 1) sum_l3[i] <= 16'd0;
            for (i = 0; i < 2;  i = i + 1) sum_l4[i] <= 16'd0;
            sum_final <= 16'd0;
            y <= 16'd0;
        end
        else begin
            // Shift delay line and insert new sample
            for (i = 39; i > 0; i = i - 1)
                delay_line[i] <= delay_line[i-1];
            delay_line[0] <= x;
            
            // Level 0: Multiply and add in pairs
            // Each product: (k+1) * tap[k], results in up to 16 bits
            // (since max product = 40 * 255 = 10200, fits in 14 bits)
            for (i = 0; i < 20; i = i + 1)
                sum_l0[i] <= (delay_line[2*i] * (2*i + 1)) + 
                             (delay_line[2*i + 1] * (2*i + 2));
            
            // Level 1: Sum pairs from level 0
            for (i = 0; i < 10; i = i + 1)
                sum_l1[i] <= sum_l0[2*i] + sum_l0[2*i + 1];
            
            // Level 2: Sum pairs from level 1
            for (i = 0; i < 5; i = i + 1)
                sum_l2[i] <= sum_l1[2*i] + sum_l1[2*i + 1];
            
            // Level 3: 5 inputs -> 3 outputs (group 2+2+1)
            sum_l3[0] <= sum_l2[0] + sum_l2[1];
            sum_l3[1] <= sum_l2[2] + sum_l2[3];
            sum_l3[2] <= sum_l2[4];
            
            // Level 4: 3 inputs -> 2 outputs
            sum_l4[0] <= sum_l3[0] + sum_l3[1];
            sum_l4[1] <= sum_l3[2];
            
            // Final level: Sum last two values
            sum_final <= sum_l4[0] + sum_l4[1];
            
            // Output register
            y <= sum_final;
        end
    end
    
endmodule