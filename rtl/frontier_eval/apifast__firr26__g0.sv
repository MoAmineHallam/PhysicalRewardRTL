module apifast__firr26__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Delay line (26 taps): tap[0] = newest sample
    reg [7:0] tap [0:25];
    
    // Pipeline registers for partial sums
    // Stage 1: multiply and add pairs (13 pairs)
    wire [15:0] stage1_sum [0:12];
    reg  [15:0] stage1_reg [0:12];
    
    // Stage 2: combine stage1 results (7 pairs)
    wire [15:0] stage2_sum [0:6];
    reg  [15:0] stage2_reg [0:6];
    
    // Stage 3: combine stage2 results (4 pairs)
    wire [15:0] stage3_sum [0:3];
    reg  [15:0] stage3_reg [0:3];
    
    // Stage 4: combine stage3 results (2 pairs)
    wire [15:0] stage4_sum [0:1];
    reg  [15:0] stage4_reg [0:1];
    
    // Stage 5: final addition
    wire [15:0] final_sum;
    reg  [15:0] final_reg;
    
    integer i;
    
    // Delay line update and reset
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 26; i = i + 1)
                tap[i] <= 8'd0;
        end else begin
            tap[0] <= x;
            for (i = 1; i < 26; i = i + 1)
                tap[i] <= tap[i-1];
        end
    end
    
    // Stage 1: Compute (k+1)*tap[k] for all taps and sum in pairs
    // For k = 0..25: coefficient = k+1, multiply 8-bit * 8-bit -> 16-bit result
    // Pairs: (0,1), (2,3), ..., (24,25) = 13 pairs
    generate
        genvar j;
        for (j = 0; j < 13; j = j + 1) begin : s1
            assign stage1_sum[j] = ( (2*j+1) * tap[2*j] ) + ( (2*j+2) * tap[2*j+1] );
        end
    endgenerate
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 13; i = i + 1)
                stage1_reg[i] <= 16'd0;
        end else begin
            for (i = 0; i < 13; i = i + 1)
                stage1_reg[i] <= stage1_sum[i];
        end
    end
    
    // Stage 2: combine 13 results into 7 (6 pairs + 1 leftover)
    // Pairs: (0,1), (2,3), (4,5), (6,7), (8,9), (10,11), (12, -) => 7 outputs
    assign stage2_sum[0] = stage1_reg[0] + stage1_reg[1];
    assign stage2_sum[1] = stage1_reg[2] + stage1_reg[3];
    assign stage2_sum[2] = stage1_reg[4] + stage1_reg[5];
    assign stage2_sum[3] = stage1_reg[6] + stage1_reg[7];
    assign stage2_sum[4] = stage1_reg[8] + stage1_reg[9];
    assign stage2_sum[5] = stage1_reg[10] + stage1_reg[11];
    assign stage2_sum[6] = stage1_reg[12];  // leftover
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 7; i = i + 1)
                stage2_reg[i] <= 16'd0;
        end else begin
            for (i = 0; i < 7; i = i + 1)
                stage2_reg[i] <= stage2_sum[i];
        end
    end
    
    // Stage 3: combine 7 results into 4 (3 pairs + 1 leftover)
    assign stage3_sum[0] = stage2_reg[0] + stage2_reg[1];
    assign stage3_sum[1] = stage2_reg[2] + stage2_reg[3];
    assign stage3_sum[2] = stage2_reg[4] + stage2_reg[5];
    assign stage3_sum[3] = stage2_reg[6];  // leftover
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 4; i = i + 1)
                stage3_reg[i] <= 16'd0;
        end else begin
            for (i = 0; i < 4; i = i + 1)
                stage3_reg[i] <= stage3_sum[i];
        end
    end
    
    // Stage 4: combine 4 results into 2
    assign stage4_sum[0] = stage3_reg[0] + stage3_reg[1];
    assign stage4_sum[1] = stage3_reg[2] + stage3_reg[3];
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 2; i = i + 1)
                stage4_reg[i] <= 16'd0;
        end else begin
            for (i = 0; i < 2; i = i + 1)
                stage4_reg[i] <= stage4_sum[i];
        end
    end
    
    // Stage 5: final addition
    assign final_sum = stage4_reg[0] + stage4_reg[1];
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            final_reg <= 16'd0;
        else
            final_reg <= final_sum;
    end
    
    // Output assignment (registered)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            y <= 16'd0;
        else
            y <= final_reg;
    end

endmodule