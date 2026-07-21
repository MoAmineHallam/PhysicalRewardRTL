module apifast__firr40__g5 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Delay line (tap 0 = newest sample)
    reg [7:0] tap [0:39];
    
    // Pipeline registers for partial sums
    // Stage 0: multiply & accumulate pairs
    reg [15:0] sum0 [0:19];  // 20 pairs
    reg [15:0] sum1 [0:9];   // 10 pairs from stage 0
    reg [15:0] sum2 [0:4];   // 5 pairs from stage 1
    reg [15:0] sum3 [0:2];   // 3 pairs (5->3 with one extra)
    reg [15:0] sum4 [0:1];   // 2 pairs from stage 3
    reg [15:0] sum5;         // final sum

    integer i;
    
    // Delay line update
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 40; i = i + 1)
                tap[i] <= 8'd0;
        end else begin
            // Shift: tap[0] gets x, others shift right
            tap[0] <= x;
            for (i = 1; i < 40; i = i + 1)
                tap[i] <= tap[i-1];
        end
    end
    
    // Stage 0: Compute 20 pairs (k, k+1) -> (k+1)*tap[k] + (k+2)*tap[k+1]
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 20; i = i + 1)
                sum0[i] <= 16'd0;
        end else begin
            for (i = 0; i < 20; i = i + 1) begin
                sum0[i] <= ((i*2+1) * tap[i*2]) + ((i*2+2) * tap[i*2+1]);
            end
        end
    end
    
    // Stage 1: sum pairs from stage 0
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 10; i = i + 1)
                sum1[i] <= 16'd0;
        end else begin
            for (i = 0; i < 10; i = i + 1)
                sum1[i] <= sum0[i*2] + sum0[i*2+1];
        end
    end
    
    // Stage 2: sum pairs from stage 1
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 5; i = i + 1)
                sum2[i] <= 16'd0;
        end else begin
            for (i = 0; i < 5; i = i + 1)
                sum2[i] <= sum1[i*2] + sum1[i*2+1];
        end
    end
    
    // Stage 3: sum pairs + one leftover (5 -> 3: 2+2+1)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 3; i = i + 1)
                sum3[i] <= 16'd0;
        end else begin
            sum3[0] <= sum2[0] + sum2[1];
            sum3[1] <= sum2[2] + sum2[3];
            sum3[2] <= sum2[4];  // leftover
        end
    end
    
    // Stage 4: sum pairs from stage 3 (3 -> 2: 1+1, one leftover)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 2; i = i + 1)
                sum4[i] <= 16'd0;
        end else begin
            sum4[0] <= sum3[0] + sum3[1];
            sum4[1] <= sum3[2];  // leftover
        end
    end
    
    // Stage 5: final sum
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sum5 <= 16'd0;
        end else begin
            sum5 <= sum4[0] + sum4[1];
        end
    end
    
    // Output register
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            y <= 16'd0;
        else
            y <= sum5;
    end

endmodule