module apifast__fir36_8b__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // --------------------------------------------------------------
    // 1. Delay line (36 samples, 8-bit each)
    // --------------------------------------------------------------
    reg [7:0] delay [0:35];
    integer i;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 36; i = i + 1)
                delay[i] <= 8'd0;
        end else begin
            // Shift: new sample enters tap0, oldest exits tap35
            delay[0] <= x;
            for (i = 1; i < 36; i = i + 1)
                delay[i] <= delay[i-1];
        end
    end

    // --------------------------------------------------------------
    // 2. Coefficients (symmetric, 18 unique values)
    // --------------------------------------------------------------
    // coeff[0] = 3,  coeff[1] = 5,  ... coeff[17] = 37
    // then mirror: coeff[18]=37, coeff[19]=35, ... coeff[35]=3
    // Since FIR is symmetric, we can pair symmetric taps to reduce
    // multiplications, but for maximum Fmax we keep direct form and
    // pipeline heavily.

    // --------------------------------------------------------------
    // 3. Pipeline stage 1: multiply each delay tap by its coefficient
    //    We use 36 parallel multipliers.
    //    Product width = 8+7 = 15 bits (max coeff 37 needs 6 bits,
    //    8*6=14 bits, plus sign? unsigned so 15 bits sufficient)
    // --------------------------------------------------------------
    reg [14:0] prod [0:35]; // product of delay[i] * coeff[i]

    // Coefficient lookup function
    function [5:0] coeff;
        input integer idx;
        begin
            if (idx < 18)
                coeff = 3 + 2*idx;          // 3,5,7,...,37
            else
                coeff = 3 + 2*(35-idx);     // mirror: 37,35,...,3
        end
    endfunction

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 36; i = i + 1)
                prod[i] <= 15'd0;
        end else begin
            for (i = 0; i < 36; i = i + 1)
                prod[i] <= delay[i] * coeff(i);
        end
    end

    // --------------------------------------------------------------
    // 4. Pipeline stage 2: sum products in a tree (reducing 36->18)
    //    Balance to keep critical path = 1 add
    // --------------------------------------------------------------
    reg [15:0] sum_stage1 [0:17]; // 18 partial sums
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 18; i = i + 1)
                sum_stage1[i] <= 16'd0;
        end else begin
            for (i = 0; i < 18; i = i + 1)
                sum_stage1[i] <= prod[2*i] + prod[2*i+1];
        end
    end

    // --------------------------------------------------------------
    // 5. Pipeline stage 3: reduce 18 -> 9
    // --------------------------------------------------------------
    reg [15:0] sum_stage2 [0:8];
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 9; i = i + 1)
                sum_stage2[i] <= 16'd0;
        end else begin
            for (i = 0; i < 9; i = i + 1)
                sum_stage2[i] <= sum_stage1[2*i] + sum_stage1[2*i+1];
        end
    end

    // --------------------------------------------------------------
    // 6. Pipeline stage 4: reduce 9 -> 5  (9 -> 4 pairs + 1 leftover)
    // --------------------------------------------------------------
    reg [15:0] sum_stage3 [0:4];
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 5; i = i + 1)
                sum_stage3[i] <= 16'd0;
        end else begin
            sum_stage3[0] <= sum_stage2[0] + sum_stage2[1];
            sum_stage3[1] <= sum_stage2[2] + sum_stage2[3];
            sum_stage3[2] <= sum_stage2[4] + sum_stage2[5];
            sum_stage3[3] <= sum_stage2[6] + sum_stage2[7];
            sum_stage3[4] <= sum_stage2[8]; // leftover
        end
    end

    // --------------------------------------------------------------
    // 7. Pipeline stage 5: reduce 5 -> 3
    // --------------------------------------------------------------
    reg [15:0] sum_stage4 [0:2];
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sum_stage4[0] <= 16'd0;
            sum_stage4[1] <= 16'd0;
            sum_stage4[2] <= 16'd0;
        end else begin
            sum_stage4[0] <= sum_stage3[0] + sum_stage3[1];
            sum_stage4[1] <= sum_stage3[2] + sum_stage3[3];
            sum_stage4[2] <= sum_stage3[4];
        end
    end

    // --------------------------------------------------------------
    // 8. Pipeline stage 6: reduce 3 -> 2
    // --------------------------------------------------------------
    reg [15:0] sum_stage5 [0:1];
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sum_stage5[0] <= 16'd0;
            sum_stage5[1] <= 16'd0;
        end else begin
            sum_stage5[0] <= sum_stage4[0] + sum_stage4[1];
            sum_stage5[1] <= sum_stage4[2];
        end
    end

    // --------------------------------------------------------------
    // 9. Pipeline stage 7: final addition -> output
    // --------------------------------------------------------------
    reg [15:0] y_int;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            y_int <= 16'd0;
        else
            y_int <= sum_stage5[0] + sum_stage5[1];
    end

    // Output register (registered)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            y <= 16'd0;
        else
            y <= y_int;
    end

endmodule