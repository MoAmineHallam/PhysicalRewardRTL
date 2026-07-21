module apifast__firr18__g4 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // --- Delay line (18 taps) ---
    reg [7:0] tap [0:17];  // tap[0] = newest sample
    
    // --- Pipeline registers for partial sums ---
    // We'll build a sum tree with 9 stages (since 18 taps)
    // Stage 1: 9 multipliers + 9 adders -> 9 partial sums (17 bits: 8b*4b max = 12b, sum of 2 = 13b)
    // Stage 2: 4 multipliers + 4 adders -> 5 partials (but we'll do balanced tree: 9->5->3->2->1)
    // Actually better: use 9 parallel multiplies, then tree add
    
    // Coefficients are k+1 for tap k, so coeff = tap_index + 1
    
    // First pipeline stage: multiply taps 0-8 and 9-17 by their coefficients
    reg [15:0] prod [0:17];  // product: 8b * 5b max = 13b, store in 16b
    
    // Second pipeline stage: first level of addition (9 sums of pairs)
    reg [15:0] sum1 [0:8];   // 9 sums
    
    // Third stage: reduce 9 -> 5 (sum1[0]+sum1[1], sum1[2]+sum1[3], sum1[4]+sum1[5], sum1[6]+sum1[7], sum1[8])
    reg [15:0] sum2 [0:4];
    
    // Fourth stage: reduce 5 -> 3
    reg [15:0] sum3 [0:2];
    
    // Fifth stage: reduce 3 -> 2
    reg [15:0] sum4 [0:1];
    
    // Sixth stage: final sum -> y
    reg [15:0] y_next;
    
    // --- Delay line update (combinational for shift, registered for tap[0]) ---
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear all taps
            for (int i = 0; i < 18; i = i + 1)
                tap[i] <= 8'd0;
            // Clear pipeline registers
            for (int i = 0; i < 18; i = i + 1)
                prod[i] <= 16'd0;
            for (int i = 0; i < 9; i = i + 1)
                sum1[i] <= 16'd0;
            for (int i = 0; i < 5; i = i + 1)
                sum2[i] <= 16'd0;
            for (int i = 0; i < 3; i = i + 1)
                sum3[i] <= 16'd0;
            for (int i = 0; i < 2; i = i + 1)
                sum4[i] <= 16'd0;
            y <= 16'd0;
        end else begin
            // Shift delay line: tap[0] gets new x, others shift
            // Note: x is registered into tap[0], rest shift on same clock
            tap[0] <= x;
            for (int i = 1; i < 18; i = i + 1)
                tap[i] <= tap[i-1];
            
            // --- Pipeline stage 1: multiply each tap by its coefficient ---
            // coeff = i+1 for tap i
            for (int i = 0; i < 18; i = i + 1)
                prod[i] <= tap[i] * (i+1);
            
            // --- Pipeline stage 2: sum pairs ---
            for (int i = 0; i < 9; i = i + 1)
                sum1[i] <= prod[2*i] + prod[2*i+1];
            
            // --- Pipeline stage 3: reduce 9 -> 5 ---
            sum2[0] <= sum1[0] + sum1[1];
            sum2[1] <= sum1[2] + sum1[3];
            sum2[2] <= sum1[4] + sum1[5];
            sum2[3] <= sum1[6] + sum1[7];
            sum2[4] <= sum1[8];  // leftover
            
            // --- Pipeline stage 4: reduce 5 -> 3 ---
            sum3[0] <= sum2[0] + sum2[1];
            sum3[1] <= sum2[2] + sum2[3];
            sum3[2] <= sum2[4];
            
            // --- Pipeline stage 5: reduce 3 -> 2 ---
            sum4[0] <= sum3[0] + sum3[1];
            sum4[1] <= sum3[2];
            
            // --- Pipeline stage 6: final sum and output ---
            y <= sum4[0] + sum4[1];
        end
    end

endmodule