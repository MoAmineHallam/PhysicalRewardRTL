module apifast__firr36__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Delay line (36 taps, 8-bit unsigned)
    reg [7:0] taps [0:35];
    
    // Pipeline registers for multiply-accumulate tree
    // Stage 1: multiply coefficients (k+1) with tap values
    // Since coefficients are constants (1..36), we can precompute partial products
    // For maximum Fmax, we'll use a 2-stage adder tree
    
    // First stage: compute 9 groups of 4 multiplications each
    wire [15:0] group_sum [0:8];
    reg [15:0] group_reg [0:8];
    
    // Second stage: sum the 9 group results using a 3-level adder tree
    reg [15:0] sum_stage1 [0:4]; // 5 intermediate results
    reg [15:0] sum_stage2 [0:2]; // 3 intermediate results
    reg [15:0] sum_stage3;       // final sum
    
    integer i;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear all taps
            for (i = 0; i < 36; i = i + 1)
                taps[i] <= 8'd0;
            
            // Clear pipeline registers
            for (i = 0; i < 9; i = i + 1)
                group_reg[i] <= 16'd0;
            
            sum_stage1[0] <= 16'd0;
            sum_stage1[1] <= 16'd0;
            sum_stage1[2] <= 16'd0;
            sum_stage1[3] <= 16'd0;
            sum_stage1[4] <= 16'd0;
            
            sum_stage2[0] <= 16'd0;
            sum_stage2[1] <= 16'd0;
            sum_stage2[2] <= 16'd0;
            
            sum_stage3 <= 16'd0;
            y <= 16'd0;
        end else begin
            // Shift delay line and insert new sample
            for (i = 35; i > 0; i = i - 1)
                taps[i] <= taps[i-1];
            taps[0] <= x;
            
            // Stage 1: Compute group sums (each group has 4 taps)
            // Group 0: taps 0-3 with coefficients 1,2,3,4
            group_reg[0] <= ({8'd0, taps[0]} * 16'd1 + 
                            {8'd0, taps[1]} * 16'd2 + 
                            {8'd0, taps[2]} * 16'd3 + 
                            {8'd0, taps[3]} * 16'd4);
            
            // Group 1: taps 4-7 with coefficients 5,6,7,8
            group_reg[1] <= ({8'd0, taps[4]} * 16'd5 + 
                            {8'd0, taps[5]} * 16'd6 + 
                            {8'd0, taps[6]} * 16'd7 + 
                            {8'd0, taps[7]} * 16'd8);
            
            // Group 2: taps 8-11 with coefficients 9,10,11,12
            group_reg[2] <= ({8'd0, taps[8]} * 16'd9 + 
                            {8'd0, taps[9]} * 16'd10 + 
                            {8'd0, taps[10]} * 16'd11 + 
                            {8'd0, taps[11]} * 16'd12);
            
            // Group 3: taps 12-15 with coefficients 13,14,15,16
            group_reg[3] <= ({8'd0, taps[12]} * 16'd13 + 
                            {8'd0, taps[13]} * 16'd14 + 
                            {8'd0, taps[14]} * 16'd15 + 
                            {8'd0, taps[15]} * 16'd16);
            
            // Group 4: taps 16-19 with coefficients 17,18,19,20
            group_reg[4] <= ({8'd0, taps[16]} * 16'd17 + 
                            {8'd0, taps[17]} * 16'd18 + 
                            {8'd0, taps[18]} * 16'd19 + 
                            {8'd0, taps[19]} * 16'd20);
            
            // Group 5: taps 20-23 with coefficients 21,22,23,24
            group_reg[5] <= ({8'd0, taps[20]} * 16'd21 + 
                            {8'd0, taps[21]} * 16'd22 + 
                            {8'd0, taps[22]} * 16'd23 + 
                            {8'd0, taps[23]} * 16'd24);
            
            // Group 6: taps 24-27 with coefficients 25,26,27,28
            group_reg[6] <= ({8'd0, taps[24]} * 16'd25 + 
                            {8'd0, taps[25]} * 16'd26 + 
                            {8'd0, taps[26]} * 16'd27 + 
                            {8'd0, taps[27]} * 16'd28);
            
            // Group 7: taps 28-31 with coefficients 29,30,31,32
            group_reg[7] <= ({8'd0, taps[28]} * 16'd29 + 
                            {8'd0, taps[29]} * 16'd30 + 
                            {8'd0, taps[30]} * 16'd31 + 
                            {8'd0, taps[31]} * 16'd32);
            
            // Group 8: taps 32-35 with coefficients 33,34,35,36
            group_reg[8] <= ({8'd0, taps[32]} * 16'd33 + 
                            {8'd0, taps[33]} * 16'd34 + 
                            {8'd0, taps[34]} * 16'd35 + 
                            {8'd0, taps[35]} * 16'd36);
            
            // Stage 2: First level of adder tree (sum pairs of groups)
            sum_stage1[0] <= group_reg[0] + group_reg[1];
            sum_stage1[1] <= group_reg[2] + group_reg[3];
            sum_stage1[2] <= group_reg[4] + group_reg[5];
            sum_stage1[3] <= group_reg[6] + group_reg[7];
            sum_stage1[4] <= group_reg[8];  // pass through, odd group
            
            // Stage 3: Second level of adder tree
            sum_stage2[0] <= sum_stage1[0] + sum_stage1[1];
            sum_stage2[1] <= sum_stage1[2] + sum_stage1[3];
            sum_stage2[2] <= sum_stage1[4];  // pass through
            
            // Stage 4: Final addition
            sum_stage3 <= sum_stage2[0] + sum_stage2[1] + sum_stage2[2];
            
            // Stage 5: Output register (take low 16 bits)
            y <= sum_stage3[15:0];
        end
    end

endmodule