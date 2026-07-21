module apifast__fir18_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // -----------------------------------------------------------------
    // Parameters
    // -----------------------------------------------------------------
    localparam TAPS = 18;  // number of taps
    localparam DIN_WIDTH = 8;
    localparam COEF_WIDTH = 5;  // max coefficient fits in 5 bits (19)
    localparam DOUT_WIDTH = 16;

    // Coefficient array (symmetric, can be used for folding but we keep direct form)
    // [3,5,7,9,11,13,15,17,19,19,17,15,13,11,9,7,5,3]
    wire [COEF_WIDTH-1:0] coeff [0:TAPS-1];
    assign coeff[0]  = 5'd3;
    assign coeff[1]  = 5'd5;
    assign coeff[2]  = 5'd7;
    assign coeff[3]  = 5'd9;
    assign coeff[4]  = 5'd11;
    assign coeff[5]  = 5'd13;
    assign coeff[6]  = 5'd15;
    assign coeff[7]  = 5'd17;
    assign coeff[8]  = 5'd19;
    assign coeff[9]  = 5'd19;
    assign coeff[10] = 5'd17;
    assign coeff[11] = 5'd15;
    assign coeff[12] = 5'd13;
    assign coeff[13] = 5'd11;
    assign coeff[14] = 5'd9;
    assign coeff[15] = 5'd7;
    assign coeff[16] = 5'd5;
    assign coeff[17] = 5'd3;

    // -----------------------------------------------------------------
    // Delay line (shift register) - 18 stages
    // -----------------------------------------------------------------
    reg [DIN_WIDTH-1:0] delay_line [0:TAPS-1];
    integer i;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < TAPS; i = i + 1)
                delay_line[i] <= 8'd0;
        end else begin
            // Shift: new sample in, oldest out
            delay_line[0] <= x;
            for (i = 1; i < TAPS; i = i + 1)
                delay_line[i] <= delay_line[i-1];
        end
    end

    // -----------------------------------------------------------------
    // Pipeline for sum-of-products
    // Strategy: 
    //   Stage 0: multiply each delay line element by coefficient (9 multiplications in parallel)
    //   Stage 1: pair-wise addition (tree reduction) -> 9 partial sums
    //   Stage 2: pair-wise addition -> 5 partial sums
    //   Stage 3: pair-wise addition -> 3 partial sums
    //   Stage 4: pair-wise addition -> 2 partial sums
    //   Stage 5: final addition -> 1 sum
    //   Stage 6: output register (low 16 bits)
    // -----------------------------------------------------------------

    // -----------------------------------------------------------------
    // Stage 0: Multiplications
    // -----------------------------------------------------------------
    reg [DIN_WIDTH+COEF_WIDTH-1:0] prod [0:TAPS-1]; // 13 bits wide
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < TAPS; i = i + 1)
                prod[i] <= 0;
        end else begin
            prod[0]  <= delay_line[0]  * coeff[0];
            prod[1]  <= delay_line[1]  * coeff[1];
            prod[2]  <= delay_line[2]  * coeff[2];
            prod[3]  <= delay_line[3]  * coeff[3];
            prod[4]  <= delay_line[4]  * coeff[4];
            prod[5]  <= delay_line[5]  * coeff[5];
            prod[6]  <= delay_line[6]  * coeff[6];
            prod[7]  <= delay_line[7]  * coeff[7];
            prod[8]  <= delay_line[8]  * coeff[8];
            prod[9]  <= delay_line[9]  * coeff[9];
            prod[10] <= delay_line[10] * coeff[10];
            prod[11] <= delay_line[11] * coeff[11];
            prod[12] <= delay_line[12] * coeff[12];
            prod[13] <= delay_line[13] * coeff[13];
            prod[14] <= delay_line[14] * coeff[14];
            prod[15] <= delay_line[15] * coeff[15];
            prod[16] <= delay_line[16] * coeff[16];
            prod[17] <= delay_line[17] * coeff[17];
        end
    end

    // -----------------------------------------------------------------
    // Stage 1: Add pairs (first reduction)
    // -----------------------------------------------------------------
    reg [DIN_WIDTH+COEF_WIDTH:0] sum1 [0:8]; // 14 bits
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 9; i = i + 1)
                sum1[i] <= 0;
        end else begin
            sum1[0] <= prod[0]  + prod[1];
            sum1[1] <= prod[2]  + prod[3];
            sum1[2] <= prod[4]  + prod[5];
            sum1[3] <= prod[6]  + prod[7];
            sum1[4] <= prod[8]  + prod[9];
            sum1[5] <= prod[10] + prod[11];
            sum1[6] <= prod[12] + prod[13];
            sum1[7] <= prod[14] + prod[15];
            sum1[8] <= prod[16] + prod[17];
        end
    end

    // -----------------------------------------------------------------
    // Stage 2: Reduce 9 sums to 5
    // -----------------------------------------------------------------
    reg [DIN_WIDTH+COEF_WIDTH+1:0] sum2 [0:4]; // 15 bits
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 5; i = i + 1)
                sum2[i] <= 0;
        end else begin
            sum2[0] <= sum1[0] + sum1[1];
            sum2[1] <= sum1[2] + sum1[3];
            sum2[2] <= sum1[4] + sum1[5];
            sum2[3] <= sum1[6] + sum1[7];
            sum2[4] <= sum1[8]; // leftover
        end
    end

    // -----------------------------------------------------------------
    // Stage 3: Reduce 5 sums to 3
    // -----------------------------------------------------------------
    reg [DIN_WIDTH+COEF_WIDTH+2:0] sum3 [0:2]; // 16 bits
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 3; i = i + 1)
                sum3[i] <= 0;
        end else begin
            sum3[0] <= sum2[0] + sum2[1];
            sum3[1] <= sum2[2] + sum2[3];
            sum3[2] <= sum2[4]; // leftover
        end
    end

    // -----------------------------------------------------------------
    // Stage 4: Reduce 3 sums to 2
    // -----------------------------------------------------------------
    reg [DIN_WIDTH+COEF_WIDTH+3:0] sum4 [0:1]; // 17 bits
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sum4[0] <= 0;
            sum4[1] <= 0;
        end else begin
            sum4[0] <= sum3[0] + sum3[1];
            sum4[1] <= sum3[2]; // leftover
        end
    end

    // -----------------------------------------------------------------
    // Stage 5: Final addition
    // -----------------------------------------------------------------
    reg [DIN_WIDTH+COEF_WIDTH+4:0] sum5; // 18 bits
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            sum5 <= 0;
        else
            sum5 <= sum4[0] + sum4[1];
    end

    // -----------------------------------------------------------------
    // Stage 6: Output (low 16 bits)
    // -----------------------------------------------------------------
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            y <= 16'd0;
        else
            y <= sum5[15:0]; // truncate to low 16 bits
    end

endmodule