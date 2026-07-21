module apifast__firr26__g3 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Delay line (shift register) - 26 taps
    reg [7:0] delay_line [0:25];
    integer k;

    // First pipeline stage: shift the delay line and compute products
    reg [15:0] prod [0:25];  // (k+1) * tap[k] for k=0..25
    
    // Second pipeline stage: partial sums (2-to-1 reduction tree)
    // Stage 2: sum pairs (13 values)
    reg [16:0] sum_stage2 [0:12];
    
    // Stage 3: sum pairs (7 values)
    reg [17:0] sum_stage3 [0:6];
    
    // Stage 4: sum pairs (4 values)
    reg [18:0] sum_stage4 [0:3];
    
    // Stage 5: sum pairs (2 values)
    reg [19:0] sum_stage5 [0:1];
    
    // Stage 6: final sum
    reg [20:0] final_sum;
    
    // Stage 7: final registered output
    reg [20:0] y_full;

    integer i;

    // Delay line update and product computation (Stage 0->1)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (k = 0; k < 26; k = k + 1) begin
                delay_line[k] <= 8'd0;
                prod[k] <= 16'd0;
            end
        end else begin
            // Shift delay line: new sample becomes tap 0
            delay_line[0] <= x;
            for (k = 1; k < 26; k = k + 1) begin
                delay_line[k] <= delay_line[k-1];
            end
            
            // Compute products (combinational read from delay_line before shift)
            // Using previous cycle's delayed values
            for (k = 0; k < 26; k = k + 1) begin
                prod[k] <= (k+1) * delay_line[k];
            end
        end
    end

    // Pipeline stage 1->2: First level of addition tree
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 13; i = i + 1)
                sum_stage2[i] <= 17'd0;
        end else begin
            for (i = 0; i < 13; i = i + 1)
                sum_stage2[i] <= prod[2*i] + prod[2*i + 1];
        end
    end

    // Pipeline stage 2->3: Second level (13 -> 7, with one pass-through)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 7; i = i + 1)
                sum_stage3[i] <= 18'd0;
        end else begin
            for (i = 0; i < 6; i = i + 1)
                sum_stage3[i] <= sum_stage2[2*i] + sum_stage2[2*i + 1];
            sum_stage3[6] <= {1'b0, sum_stage2[12]};  // Pass through with sign extension
        end
    end

    // Pipeline stage 3->4: Third level (7 -> 4)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 4; i = i + 1)
                sum_stage4[i] <= 19'd0;
        end else begin
            for (i = 0; i < 3; i = i + 1)
                sum_stage4[i] <= sum_stage3[2*i] + sum_stage3[2*i + 1];
            sum_stage4[3] <= {1'b0, sum_stage3[6]};  // Pass through
        end
    end

    // Pipeline stage 4->5: Fourth level (4 -> 2)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sum_stage5[0] <= 20'd0;
            sum_stage5[1] <= 20'd0;
        end else begin
            sum_stage5[0] <= sum_stage4[0] + sum_stage4[1];
            sum_stage5[1] <= sum_stage4[2] + sum_stage4[3];
        end
    end

    // Pipeline stage 5->6: Fifth level (2 -> 1)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            final_sum <= 21'd0;
        else
            final_sum <= sum_stage5[0] + sum_stage5[1];
    end

    // Pipeline stage 6->7: Final output register with truncation to 16 bits
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            y <= 16'd0;
        else
            y <= final_sum[15:0];
    end

endmodule