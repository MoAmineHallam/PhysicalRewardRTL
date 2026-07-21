module apifast__firr18__g3 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Delay line: tap[0] = newest sample (current x)
    reg [7:0] tap [0:17];
    integer i;

    // Pipeline registers for partial sums and products
    reg [15:0] sum_stage1 [0:8];  // 9 partial sums after first add stage
    reg [15:0] sum_stage2 [0:4];  // 5 partial sums after second add stage
    reg [15:0] sum_stage3 [0:2];  // 3 partial sums after third add stage
    reg [15:0] sum_stage4 [0:1];  // 2 partial sums after fourth add stage
    reg [15:0] sum_stage5;        // final sum

    // Coefficient multipliers (precompute to avoid logic)
    // k+1 for k=0..17
    wire [4:0] coeff [0:17];
    assign coeff[0]  = 5'd1;
    assign coeff[1]  = 5'd2;
    assign coeff[2]  = 5'd3;
    assign coeff[3]  = 5'd4;
    assign coeff[4]  = 5'd5;
    assign coeff[5]  = 5'd6;
    assign coeff[6]  = 5'd7;
    assign coeff[7]  = 5'd8;
    assign coeff[8]  = 5'd9;
    assign coeff[9]  = 5'd10;
    assign coeff[10] = 5'd11;
    assign coeff[11] = 5'd12;
    assign coeff[12] = 5'd13;
    assign coeff[13] = 5'd14;
    assign coeff[14] = 5'd15;
    assign coeff[15] = 5'd16;
    assign coeff[16] = 5'd17;
    assign coeff[17] = 5'd18;

    // Product registers (first pipeline stage)
    reg [15:0] prod [0:17];
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 18; i = i + 1) begin
                tap[i] <= 8'd0;
                prod[i] <= 16'd0;
            end
        end else begin
            // Shift delay line
            for (i = 17; i > 0; i = i - 1) begin
                tap[i] <= tap[i-1];
            end
            tap[0] <= x;

            // Compute products (1 multiply per tap)
            for (i = 0; i < 18; i = i + 1) begin
                prod[i] <= tap[i] * coeff[i];
            end
        end
    end

    // Stage 1: sum pairs of products (9 additions)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 9; i = i + 1)
                sum_stage1[i] <= 16'd0;
        end else begin
            for (i = 0; i < 9; i = i + 1)
                sum_stage1[i] <= prod[2*i] + prod[2*i+1];
        end
    end

    // Stage 2: sum pairs from stage1 (5 additions: 4 pairs + 1 leftover)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 5; i = i + 1)
                sum_stage2[i] <= 16'd0;
        end else begin
            sum_stage2[0] <= sum_stage1[0] + sum_stage1[1];
            sum_stage2[1] <= sum_stage1[2] + sum_stage1[3];
            sum_stage2[2] <= sum_stage1[4] + sum_stage1[5];
            sum_stage2[3] <= sum_stage1[6] + sum_stage1[7];
            sum_stage2[4] <= sum_stage1[8];  // leftover
        end
    end

    // Stage 3: sum pairs from stage2 (3 additions)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 3; i = i + 1)
                sum_stage3[i] <= 16'd0;
        end else begin
            sum_stage3[0] <= sum_stage2[0] + sum_stage2[1];
            sum_stage3[1] <= sum_stage2[2] + sum_stage2[3];
            sum_stage3[2] <= sum_stage2[4];  // leftover
        end
    end

    // Stage 4: sum pairs from stage3 (2 additions)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sum_stage4[0] <= 16'd0;
            sum_stage4[1] <= 16'd0;
        end else begin
            sum_stage4[0] <= sum_stage3[0] + sum_stage3[1];
            sum_stage4[1] <= sum_stage3[2];  // leftover
        end
    end

    // Stage 5: final addition
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sum_stage5 <= 16'd0;
        end else begin
            sum_stage5 <= sum_stage4[0] + sum_stage4[1];
        end
    end

    // Output register (low 16 bits of sum)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            y <= 16'd0;
        else
            y <= sum_stage5;
    end

endmodule