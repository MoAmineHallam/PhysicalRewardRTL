module apifast__fir6_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Delay line registers (6 taps)
    reg [7:0] delay0, delay1, delay2, delay3, delay4, delay5;
    
    // Pipeline registers for multiplication results (stage 1)
    reg [15:0] mult0, mult1, mult2, mult3, mult4, mult5;
    
    // Pipeline registers for partial sums (stage 2)
    reg [15:0] sum01, sum23, sum45;
    
    // Pipeline register for final sum (stage 3)
    reg [15:0] sum0123, sum_sum45;
    
    // Stage 4: final output register (y)
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear all registers
            delay0 <= 8'd0;
            delay1 <= 8'd0;
            delay2 <= 8'd0;
            delay3 <= 8'd0;
            delay4 <= 8'd0;
            delay5 <= 8'd0;
            
            mult0 <= 16'd0;
            mult1 <= 16'd0;
            mult2 <= 16'd0;
            mult3 <= 16'd0;
            mult4 <= 16'd0;
            mult5 <= 16'd0;
            
            sum01 <= 16'd0;
            sum23 <= 16'd0;
            sum45 <= 16'd0;
            
            sum0123 <= 16'd0;
            sum_sum45 <= 16'd0;
            
            y <= 16'd0;
        end else begin
            // Stage 0: Shift delay line and load new sample
            delay5 <= delay4;
            delay4 <= delay3;
            delay3 <= delay2;
            delay2 <= delay1;
            delay1 <= delay0;
            delay0 <= x;
            
            // Stage 1: Multiply each delay tap by its coefficient
            // Coefficients: [3, 5, 7, 7, 5, 3]
            mult0 <= delay0 * 8'd3;   // actually delay0 is from previous cycle, correct
            mult1 <= delay1 * 8'd5;
            mult2 <= delay2 * 8'd7;
            mult3 <= delay3 * 8'd7;
            mult4 <= delay4 * 8'd5;
            mult5 <= delay5 * 8'd3;
            
            // Stage 2: Pairwise additions
            sum01 <= mult0 + mult1;
            sum23 <= mult2 + mult3;
            sum45 <= mult4 + mult5;
            
            // Stage 3: Combine pairwise sums
            sum0123 <= sum01 + sum23;
            sum_sum45 <= sum45;  // pipeline register for alignment
            
            // Stage 4: Final addition and output (low 16 bits)
            y <= sum0123 + sum_sum45;
        end
    end

endmodule