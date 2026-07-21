module apifast__firr10__g2 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Delay line: 10 taps (tap0 = newest = current x)
    reg [7:0] tap [0:9];
    
    // Two-stage pipelined multipliers and adders
    // Stage 1: multiply each tap by its coefficient (k+1)
    wire [15:0] mul [0:9];
    genvar i;
    generate
        for (i = 0; i < 10; i = i + 1) begin : mul_stage
            // Coefficient = i+1 (max 10 * 255 = 2550 fits in 12 bits, pad to 16)
            wire [11:0] coeff = i + 1;
            reg  [15:0] mul_reg;
            always @(posedge clk or negedge rst_n) begin
                if (!rst_n)
                    mul_reg <= 16'd0;
                else
                    mul_reg <= tap[i] * coeff;
            end
            assign mul[i] = mul_reg;
        end
    endgenerate

    // Stage 2: Adder tree (balanced, pipelined)
    // First level: 5 sums of pairs
    reg [15:0] sum_l1 [0:4];
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sum_l1[0] <= 16'd0;
            sum_l1[1] <= 16'd0;
            sum_l1[2] <= 16'd0;
            sum_l1[3] <= 16'd0;
            sum_l1[4] <= 16'd0;
        end else begin
            sum_l1[0] <= mul[0] + mul[1];
            sum_l1[1] <= mul[2] + mul[3];
            sum_l1[2] <= mul[4] + mul[5];
            sum_l1[3] <= mul[6] + mul[7];
            sum_l1[4] <= mul[8] + mul[9];
        end
    end

    // Second level: 3 sums (2 pairs + 1 leftover carried from previous)
    reg [15:0] sum_l2 [0:2];
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sum_l2[0] <= 16'd0;
            sum_l2[1] <= 16'd0;
            sum_l2[2] <= 16'd0;
        end else begin
            sum_l2[0] <= sum_l1[0] + sum_l1[1];
            sum_l2[1] <= sum_l1[2] + sum_l1[3];
            sum_l2[2] <= sum_l1[4];  // single from previous stage
        end
    end

    // Third level: 2 sums
    reg [15:0] sum_l3 [0:1];
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sum_l3[0] <= 16'd0;
            sum_l3[1] <= 16'd0;
        end else begin
            sum_l3[0] <= sum_l2[0] + sum_l2[1];
            sum_l3[1] <= sum_l2[2];
        end
    end

    // Final output register (taking low 16 bits)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            y <= 16'd0;
        else
            y <= sum_l3[0] + sum_l3[1];
    end

    // Delay line update: shift on posedge clk
    integer j;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (j = 0; j < 10; j = j + 1)
                tap[j] <= 8'd0;
        end else begin
            tap[0] <= x;
            for (j = 1; j < 10; j = j + 1)
                tap[j] <= tap[j-1];
        end
    end

endmodule