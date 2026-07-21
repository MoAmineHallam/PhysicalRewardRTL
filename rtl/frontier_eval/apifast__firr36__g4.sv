module apifast__firr36__g4 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // 36-tap delay line (tap 0 = newest sample)
    reg [7:0] tap [0:35];
    
    // Pipeline registers for partial sums
    // We'll use a tree-adder structure to minimize critical path
    // Stage 1: multiply each tap by coefficient (k+1) and compute initial pairs
    // Stage 2-5: add pairs in tree fashion
    
    // Stage 0: Load new sample and shift delay line
    integer i;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 36; i = i + 1)
                tap[i] <= 8'd0;
        end else begin
            // Shift delay line: tap[35] gets old tap[34], etc.
            for (i = 35; i > 0; i = i - 1)
                tap[i] <= tap[i-1];
            // New sample enters tap 0
            tap[0] <= x;
        end
    end
    
    // ------------------------------------------------------------------
    // Pipeline stage 1: multiply each tap by coefficient (k+1)
    // Coefficient for tap k is (k+1) -- max coefficient = 36 = 6'h24
    // Product is 8-bit * 6-bit = up to 14 bits, but we'll keep full precision
    // Use registered multipliers at first pipeline stage
    // ------------------------------------------------------------------
    reg [13:0] prod [0:35]; // 14 bits sufficient: 255*36 = 9180 (14 bits)
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 36; i = i + 1)
                prod[i] <= 14'd0;
        end else begin
            for (i = 0; i < 36; i = i + 1)
                prod[i] <= tap[i] * (i+1);
        end
    end
    
    // ------------------------------------------------------------------
    // Pipeline stages 2-5: tree adder
    // We have 36 products to sum. Use binary tree:
    // Stage 2: 18 sums of pairs
    // Stage 3: 9 sums of pairs
    // Stage 4: 5 sums (4 from pairs + 1 leftover)
    // Stage 5: 3 sums (2 pairs + 1 leftover)
    // Stage 6: 2 sums (1 pair + 1 leftover)
    // Stage 7: final sum
    //
    // To meet timing we'll keep each stage adding at most 2 numbers.
    // ------------------------------------------------------------------
    
    // Stage 2: pair sums (18 results)
    reg [14:0] sum2 [0:17]; // 14+1 = 15 bits for carry
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 18; i = i + 1)
                sum2[i] <= 15'd0;
        end else begin
            for (i = 0; i < 18; i = i + 1)
                sum2[i] <= prod[2*i] + prod[2*i+1];
        end
    end
    
    // Stage 3: 9 sums (pairs from sum2)
    reg [15:0] sum3 [0:8];
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 9; i = i + 1)
                sum3[i] <= 16'd0;
        end else begin
            for (i = 0; i < 9; i = i + 1)
                sum3[i] <= sum2[2*i] + sum2[2*i+1];
        end
    end
    
    // Stage 4: 5 sums (4 from pairs + 1 leftover from sum3[8])
    reg [16:0] sum4 [0:4];
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 5; i = i + 1)
                sum4[i] <= 17'd0;
        end else begin
            sum4[0] <= sum3[0] + sum3[1];
            sum4[1] <= sum3[2] + sum3[3];
            sum4[2] <= sum3[4] + sum3[5];
            sum4[3] <= sum3[6] + sum3[7];
            sum4[4] <= {1'b0, sum3[8]}; // extend to 17 bits
        end
    end
    
    // Stage 5: 3 sums (2 pairs + 1 leftover)
    reg [17:0] sum5 [0:2];
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 3; i = i + 1)
                sum5[i] <= 18'd0;
        end else begin
            sum5[0] <= sum4[0] + sum4[1];
            sum5[1] <= sum4[2] + sum4[3];
            sum5[2] <= {1'b0, sum4[4]}; // extend to 18 bits
        end
    end
    
    // Stage 6: 2 sums (1 pair + 1 leftover)
    reg [18:0] sum6 [0:1];
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sum6[0] <= 19'd0;
            sum6[1] <= 19'd0;
        end else begin
            sum6[0] <= sum5[0] + sum5[1];
            sum6[1] <= {1'b0, sum5[2]}; // extend to 19 bits
        end
    end
    
    // Stage 7: final sum and output
    reg [19:0] sum_final;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sum_final <= 20'd0;
            y <= 16'd0;
        end else begin
            sum_final <= sum6[0] + sum6[1];
            // Take low 16 bits (truncation)
            y <= sum_final[15:0];
        end
    end

endmodule