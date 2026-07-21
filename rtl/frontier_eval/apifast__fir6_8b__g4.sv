module apifast__fir6_8b__g4 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Delay line (6 stages)
    reg [7:0] delay [0:5];
    
    // Pipeline stages for multiplication and addition
    // Stage 1: Multiplications (coefficients [3,5,7,7,5,3])
    reg [15:0] m0, m1, m2, m3, m4, m5;
    
    // Stage 2: First level of additions (3 pairs)
    reg [16:0] a0, a1, a2;
    
    // Stage 3: Second level addition
    reg [17:0] b0, b1;
    
    // Stage 4: Final addition and output
    reg [18:0] sum;
    
    integer i;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Reset delay line
            for (i = 0; i < 6; i = i + 1)
                delay[i] <= 8'd0;
            
            // Reset all pipeline registers
            m0 <= 16'd0; m1 <= 16'd0; m2 <= 16'd0;
            m3 <= 16'd0; m4 <= 16'd0; m5 <= 16'd0;
            a0 <= 17'd0; a1 <= 17'd0; a2 <= 17'd0;
            b0 <= 18'd0; b1 <= 18'd0;
            sum <= 19'd0;
            y <= 16'd0;
        end else begin
            // Shift delay line and insert new sample
            delay[0] <= x;
            for (i = 1; i < 6; i = i + 1)
                delay[i] <= delay[i-1];
            
            // Stage 1: Multiply each delay element by its coefficient
            m0 <= {delay[0], 1'b0} + delay[0];                    // *3 = *2 + *1
            m1 <= {delay[1], 2'b00} + delay[1];                   // *5 = *4 + *1
            m2 <= {delay[2], 3'b000} - delay[2];                  // *7 = *8 - *1
            m3 <= {delay[3], 3'b000} - delay[3];                  // *7 = *8 - *1
            m4 <= {delay[4], 2'b00} + delay[4];                   // *5 = *4 + *1
            m5 <= {delay[5], 1'b0} + delay[5];                    // *3 = *2 + *1
            
            // Stage 2: First level addition (pairs)
            a0 <= m0 + m5;  // [0] + [5]
            a1 <= m1 + m4;  // [1] + [4]
            a2 <= m2 + m3;  // [2] + [3]
            
            // Stage 3: Second level addition
            b0 <= a0 + a1;  // ([0]+[5]) + ([1]+[4])
            b1 <= a2;       // Pass through ([2]+[3])
            
            // Stage 4: Final addition and output
            sum <= b0 + b1;  // Complete sum
            y <= sum[15:0];  // Take low 16 bits
        end
    end

endmodule