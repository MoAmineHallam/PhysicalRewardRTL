module apifast__firr36__g5 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Delay line: 36 taps, newest = tap0
    reg [7:0] tap [0:35];
    
    // Pipeline registers for partial sums
    reg [31:0] sum0, sum1, sum2, sum3, sum4, sum5;
    reg [31:0] sum6, sum7, sum8, sum9, sum10, sum11;
    reg [31:0] sum12, sum13, sum14, sum15, sum16, sum17;
    reg [31:0] sum18, sum19, sum20, sum21, sum22, sum23;
    reg [31:0] sum24, sum25, sum26, sum27, sum28, sum29;
    reg [31:0] sum30, sum31, sum32, sum33, sum34, sum35;
    
    // Stage 1 pipeline registers
    reg [31:0] p1_0, p1_1, p1_2, p1_3, p1_4, p1_5;
    reg [31:0] p1_6, p1_7, p1_8, p1_9, p1_10, p1_11;
    reg [31:0] p1_12, p1_13, p1_14, p1_15, p1_16, p1_17;
    
    // Stage 2 pipeline registers
    reg [31:0] p2_0, p2_1, p2_2, p2_3, p2_4, p2_5;
    reg [31:0] p2_6, p2_7, p2_8;
    
    // Stage 3 pipeline registers
    reg [31:0] p3_0, p3_1, p3_2, p3_3, p3_4;
    
    // Stage 4 pipeline registers
    reg [31:0] p4_0, p4_1, p4_2;
    
    // Stage 5 pipeline registers
    reg [31:0] p5_0, p5_1;
    
    // Stage 6 pipeline register
    reg [31:0] p6_0;
    
    integer i;
    
    // Shift register and multiply-accumulate pipeline
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear all delay line
            for (i = 0; i < 36; i = i + 1)
                tap[i] <= 8'd0;
            
            // Clear all pipeline registers
            sum0 <= 32'd0; sum1 <= 32'd0; sum2 <= 32'd0; 
            sum3 <= 32'd0; sum4 <= 32'd0; sum5 <= 32'd0;
            sum6 <= 32'd0; sum7 <= 32'd0; sum8 <= 32'd0;
            sum9 <= 32'd0; sum10 <= 32'd0; sum11 <= 32'd0;
            sum12 <= 32'd0; sum13 <= 32'd0; sum14 <= 32'd0;
            sum15 <= 32'd0; sum16 <= 32'd0; sum17 <= 32'd0;
            sum18 <= 32'd0; sum19 <= 32'd0; sum20 <= 32'd0;
            sum21 <= 32'd0; sum22 <= 32'd0; sum23 <= 32'd0;
            sum24 <= 32'd0; sum25 <= 32'd0; sum26 <= 32'd0;
            sum27 <= 32'd0; sum28 <= 32'd0; sum29 <= 32'd0;
            sum30 <= 32'd0; sum31 <= 32'd0; sum32 <= 32'd0;
            sum33 <= 32'd0; sum34 <= 32'd0; sum35 <= 32'd0;
            
            p1_0 <= 32'd0; p1_1 <= 32'd0; p1_2 <= 32'd0; 
            p1_3 <= 32'd0; p1_4 <= 32'd0; p1_5 <= 32'd0;
            p1_6 <= 32'd0; p1_7 <= 32'd0; p1_8 <= 32'd0;
            p1_9 <= 32'd0; p1_10 <= 32'd0; p1_11 <= 32'd0;
            p1_12 <= 32'd0; p1_13 <= 32'd0; p1_14 <= 32'd0;
            p1_15 <= 32'd0; p1_16 <= 32'd0; p1_17 <= 32'd0;
            
            p2_0 <= 32'd0; p2_1 <= 32'd0; p2_2 <= 32'd0;
            p2_3 <= 32'd0; p2_4 <= 32'd0; p2_5 <= 32'd0;
            p2_6 <= 32'd0; p2_7 <= 32'd0; p2_8 <= 32'd0;
            
            p3_0 <= 32'd0; p3_1 <= 32'd0; p3_2 <= 32'd0;
            p3_3 <= 32'd0; p3_4 <= 32'd0;
            
            p4_0 <= 32'd0; p4_1 <= 32'd0; p4_2 <= 32'd0;
            
            p5_0 <= 32'd0; p5_1 <= 32'd0;
            
            p6_0 <= 32'd0;
            
            y <= 16'd0;
        end else begin
            // Shift delay line and insert new sample
            tap[0] <= x;
            for (i = 1; i < 36; i = i + 1)
                tap[i] <= tap[i-1];
            
            // Stage 0: multiply each tap by coefficient (k+1)
            sum0  <= tap[0]  * 1;
            sum1  <= tap[1]  * 2;
            sum2  <= tap[2]  * 3;
            sum3  <= tap[3]  * 4;
            sum4  <= tap[4]  * 5;
            sum5  <= tap[5]  * 6;
            sum6  <= tap[6]  * 7;
            sum7  <= tap[7]  * 8;
            sum8  <= tap[8]  * 9;
            sum9  <= tap[9]  * 10;
            sum10 <= tap[10] * 11;
            sum11 <= tap[11] * 12;
            sum12 <= tap[12] * 13;
            sum13 <= tap[13] * 14;
            sum14 <= tap[14] * 15;
            sum15 <= tap[15] * 16;
            sum16 <= tap[16] * 17;
            sum17 <= tap[17] * 18;
            sum18 <= tap[18] * 19;
            sum19 <= tap[19] * 20;
            sum20 <= tap[20] * 21;
            sum21 <= tap[21] * 22;
            sum22 <= tap[22] * 23;
            sum23 <= tap[23] * 24;
            sum24 <= tap[24] * 25;
            sum25 <= tap[25] * 26;
            sum26 <= tap[26] * 27;
            sum27 <= tap[27] * 28;
            sum28 <= tap[28] * 29;
            sum29 <= tap[29] * 30;
            sum30 <= tap[30] * 31;
            sum31 <= tap[31] * 32;
            sum32 <= tap[32] * 33;
            sum33 <= tap[33] * 34;
            sum34 <= tap[34] * 35;
            sum35 <= tap[35] * 36;
            
            // Stage 1: sum pairs (18 adders)
            p1_0  <= sum0  + sum1;
            p1_1  <= sum2  + sum3;
            p1_2  <= sum4  + sum5;
            p1_3  <= sum6  + sum7;
            p1_4  <= sum8  + sum9;
            p1_5  <= sum10 + sum11;
            p1_6  <= sum12 + sum13;
            p1_7  <= sum14 + sum15;
            p1_8  <= sum16 + sum17;
            p1_9  <= sum18 + sum19;
            p1_10 <= sum20 + sum21;
            p1_11 <= sum22 + sum23;
            p1_12 <= sum24 + sum25;
            p1_13 <= sum26 + sum27;
            p1_14 <= sum28 + sum29;
            p1_15 <= sum30 + sum31;
            p1_16 <= sum32 + sum33;
            p1_17 <= sum34 + sum35;
            
            // Stage 2: sum groups of 4 (9 adders)
            p2_0 <= p1_0  + p1_1;
            p2_1 <= p1_2  + p1_3;
            p2_2 <= p1_4  + p1_5;
            p2_3 <= p1_6  + p1_7;
            p2_4 <= p1_8  + p1_9;
            p2_5 <= p1_10 + p1_11;
            p2_6 <= p1_12 + p1_13;
            p2_7 <= p1_14 + p1_15;
            p2_8 <= p1_16 + p1_17;
            
            // Stage 3: sum groups of 8 (5 adders)
            p3_0 <= p2_0 + p2_1;
            p3_1 <= p2_2 + p2_3;
            p3_2 <= p2_4 + p2_5;
            p3_3 <= p2_6 + p2_7;
            p3_4 <= p2_8;  // single, just pass through
            
            // Stage 4: sum groups of 16 (3 adders)
            p4_0 <= p3_0 + p3_1;
            p4_1 <= p3_2 + p3_3;
            p4_2 <= p3_4;  // pass through
            
            // Stage 5: sum groups of 32 (2 adders)
            p5_0 <= p4_0 + p4_1;
            p5_1 <= p4_2;  // pass through
            
            // Stage 6: final sum (1 adder)
            p6_0 <= p5_0 + p5_1;
            
            // Output: take low 16 bits
            y <= p6_0[15:0];
        end
    end

endmodule