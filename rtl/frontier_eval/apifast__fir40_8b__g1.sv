module apifast__fir40_8b__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Delay line: 40 samples, each 8-bit unsigned
    reg [7:0] delay_line [0:39];
    integer i;

    // Fixed coefficients (symmetric)
    // [3,5,7,9,11,13,15,17,19,21,23,25,27,29,31,33,35,37,39,41,
    //  41,39,37,35,33,31,29,27,25,23,21,19,17,15,13,11,9,7,5,3]
    wire [5:0] coeff [0:39];
    assign coeff[0]  = 6'd3;
    assign coeff[1]  = 6'd5;
    assign coeff[2]  = 6'd7;
    assign coeff[3]  = 6'd9;
    assign coeff[4]  = 6'd11;
    assign coeff[5]  = 6'd13;
    assign coeff[6]  = 6'd15;
    assign coeff[7]  = 6'd17;
    assign coeff[8]  = 6'd19;
    assign coeff[9]  = 6'd21;
    assign coeff[10] = 6'd23;
    assign coeff[11] = 6'd25;
    assign coeff[12] = 6'd27;
    assign coeff[13] = 6'd29;
    assign coeff[14] = 6'd31;
    assign coeff[15] = 6'd33;
    assign coeff[16] = 6'd35;
    assign coeff[17] = 6'd37;
    assign coeff[18] = 6'd39;
    assign coeff[19] = 6'd41;
    assign coeff[20] = 6'd41;
    assign coeff[21] = 6'd39;
    assign coeff[22] = 6'd37;
    assign coeff[23] = 6'd35;
    assign coeff[24] = 6'd33;
    assign coeff[25] = 6'd31;
    assign coeff[26] = 6'd29;
    assign coeff[27] = 6'd27;
    assign coeff[28] = 6'd25;
    assign coeff[29] = 6'd23;
    assign coeff[30] = 6'd21;
    assign coeff[31] = 6'd19;
    assign coeff[32] = 6'd17;
    assign coeff[33] = 6'd15;
    assign coeff[34] = 6'd13;
    assign coeff[35] = 6'd11;
    assign coeff[36] = 6'd9;
    assign coeff[37] = 6'd7;
    assign coeff[38] = 6'd5;
    assign coeff[39] = 6'd3;

    // Stage 1: Multiply each sample by coefficient (pipelined)
    reg [13:0] mul_stage1 [0:39];
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 40; i = i + 1) begin
                mul_stage1[i] <= 14'd0;
            end
        end else begin
            for (i = 0; i < 40; i = i + 1) begin
                mul_stage1[i] <= delay_line[i] * coeff[i];
            end
        end
    end

    // Stage 2: Pairwise addition tree (pipelined)
    // 40 -> 20 -> 10 -> 5 -> 3 -> 2 -> 1
    reg [15:0] sum_stage2 [0:19];
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 20; i = i + 1) begin
                sum_stage2[i] <= 16'd0;
            end
        end else begin
            for (i = 0; i < 20; i = i + 1) begin
                sum_stage2[i] <= mul_stage1[2*i] + mul_stage1[2*i+1];
            end
        end
    end

    reg [15:0] sum_stage3 [0:9];
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 10; i = i + 1) begin
                sum_stage3[i] <= 16'd0;
            end
        end else begin
            for (i = 0; i < 10; i = i + 1) begin
                sum_stage3[i] <= sum_stage2[2*i] + sum_stage2[2*i+1];
            end
        end
    end

    reg [15:0] sum_stage4 [0:4];
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 5; i = i + 1) begin
                sum_stage4[i] <= 16'd0;
            end
        end else begin
            for (i = 0; i < 5; i = i + 1) begin
                sum_stage4[i] <= sum_stage3[2*i] + sum_stage3[2*i+1];
            end
        end
    end

    // Stage 5: 5 inputs -> 3 (2 + 2 + 1)
    reg [15:0] sum_stage5 [0:2];
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sum_stage5[0] <= 16'd0;
            sum_stage5[1] <= 16'd0;
            sum_stage5[2] <= 16'd0;
        end else begin
            sum_stage5[0] <= sum_stage4[0] + sum_stage4[1];
            sum_stage5[1] <= sum_stage4[2] + sum_stage4[3];
            sum_stage5[2] <= sum_stage4[4];
        end
    end

    // Stage 6: 3 inputs -> 2
    reg [15:0] sum_stage6 [0:1];
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sum_stage6[0] <= 16'd0;
            sum_stage6[1] <= 16'd0;
        end else begin
            sum_stage6[0] <= sum_stage5[0] + sum_stage5[1];
            sum_stage6[1] <= sum_stage5[2];
        end
    end

    // Stage 7: Final addition and output register
    reg [15:0] sum_final;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sum_final <= 16'd0;
            y <= 16'd0;
        end else begin
            sum_final <= sum_stage6[0] + sum_stage6[1];
            y <= sum_final;
        end
    end

    // Delay line update (registered)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 40; i = i + 1) begin
                delay_line[i] <= 8'd0;
            end
        end else begin
            delay_line[0] <= x;
            for (i = 1; i < 40; i = i + 1) begin
                delay_line[i] <= delay_line[i-1];
            end
        end
    end

endmodule