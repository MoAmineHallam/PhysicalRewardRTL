module apifast__firr36__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // 36-tap delay line (unsigned 8-bit)
    reg [7:0] tap [0:35];
    integer i;

    // Pipeline registers for partial sums
    reg [15:0] sum_stage0 [0:17];  // 18 parallel multiplies
    reg [15:0] sum_stage1 [0:8];   // 9 additions
    reg [15:0] sum_stage2 [0:4];   // 5 additions
    reg [15:0] sum_stage3 [0:2];   // 3 additions
    reg [15:0] sum_stage4 [0:1];   // 2 additions
    reg [15:0] sum_final;          // final sum before output

    // Shift register for delay line
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 36; i = i + 1)
                tap[i] <= 8'd0;
        end else begin
            // Shift: newest sample goes to tap[0]
            for (i = 35; i > 0; i = i - 1)
                tap[i] <= tap[i-1];
            tap[0] <= x;
        end
    end

    // Stage 0: 18 parallel multiply-accumulate pairs
    // Each computes (k+1)*tap[k] + (k+19)*tap[k+18] for k=0..17
    // Coefficients: k+1 and k+19
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 18; i = i + 1)
                sum_stage0[i] <= 16'd0;
        end else begin
            for (i = 0; i < 18; i = i + 1)
                sum_stage0[i] <= (i+1) * tap[i] + (i+19) * tap[i+18];
        end
    end

    // Stage 1: 9 additions (pair up stage0 results)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 9; i = i + 1)
                sum_stage1[i] <= 16'd0;
        end else begin
            for (i = 0; i < 9; i = i + 1)
                sum_stage1[i] <= sum_stage0[2*i] + sum_stage0[2*i+1];
        end
    end

    // Stage 2: 5 additions (pair up stage1, one unused)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 5; i = i + 1)
                sum_stage2[i] <= 16'd0;
        end else begin
            for (i = 0; i < 4; i = i + 1)
                sum_stage2[i] <= sum_stage1[2*i] + sum_stage1[2*i+1];
            sum_stage2[4] <= sum_stage1[8]; // odd leftover
        end
    end

    // Stage 3: 3 additions (pair up stage2)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 3; i = i + 1)
                sum_stage3[i] <= 16'd0;
        end else begin
            sum_stage3[0] <= sum_stage2[0] + sum_stage2[1];
            sum_stage3[1] <= sum_stage2[2] + sum_stage2[3];
            sum_stage3[2] <= sum_stage2[4]; // odd leftover
        end
    end

    // Stage 4: 2 additions (pair up stage3)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sum_stage4[0] <= 16'd0;
            sum_stage4[1] <= 16'd0;
        end else begin
            sum_stage4[0] <= sum_stage3[0] + sum_stage3[1];
            sum_stage4[1] <= sum_stage3[2]; // odd leftover
        end
    end

    // Stage 5: final addition
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            sum_final <= 16'd0;
        else
            sum_final <= sum_stage4[0] + sum_stage4[1];
    end

    // Output register
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            y <= 16'd0;
        else
            y <= sum_final;
    end

endmodule