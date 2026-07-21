module apifast__fir26_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Delay line registers (26 stages)
    reg [7:0] dly [0:25];
    
    // First stage multipliers - 13 parallel multiplications
    wire [15:0] m0, m1, m2, m3, m4, m5, m6, m7, m8, m9, m10, m11, m12;
    reg [15:0] m0_r, m1_r, m2_r, m3_r, m4_r, m5_r, m6_r, m7_r, m8_r, m9_r, m10_r, m11_r, m12_r;
    
    // Symmetric coefficient pairs (reduced from 26 to 13 multiplications)
    assign m0 = dly[0] * 8'd3 + dly[25] * 8'd3;
    assign m1 = dly[1] * 8'd5 + dly[24] * 8'd5;
    assign m2 = dly[2] * 8'd7 + dly[23] * 8'd7;
    assign m3 = dly[3] * 8'd9 + dly[22] * 8'd9;
    assign m4 = dly[4] * 8'd11 + dly[21] * 8'd11;
    assign m5 = dly[5] * 8'd13 + dly[20] * 8'd13;
    assign m6 = dly[6] * 8'd15 + dly[19] * 8'd15;
    assign m7 = dly[7] * 8'd17 + dly[18] * 8'd17;
    assign m8 = dly[8] * 8'd19 + dly[17] * 8'd19;
    assign m9 = dly[9] * 8'd21 + dly[16] * 8'd21;
    assign m10 = dly[10] * 8'd23 + dly[15] * 8'd23;
    assign m11 = dly[11] * 8'd25 + dly[14] * 8'd25;
    assign m12 = dly[12] * 8'd27 + dly[13] * 8'd27;
    
    // Pipeline stage 1: Register multiplier outputs
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            m0_r <= 16'd0; m1_r <= 16'd0; m2_r <= 16'd0; m3_r <= 16'd0;
            m4_r <= 16'd0; m5_r <= 16'd0; m6_r <= 16'd0; m7_r <= 16'd0;
            m8_r <= 16'd0; m9_r <= 16'd0; m10_r <= 16'd0; m11_r <= 16'd0;
            m12_r <= 16'd0;
        end else begin
            m0_r <= m0; m1_r <= m1; m2_r <= m2; m3_r <= m3;
            m4_r <= m4; m5_r <= m5; m6_r <= m6; m7_r <= m7;
            m8_r <= m8; m9_r <= m9; m10_r <= m10; m11_r <= m11;
            m12_r <= m12;
        end
    end
    
    // First adder tree stage (7 additions)
    reg [16:0] a0, a1, a2, a3, a4, a5, a6;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            a0 <= 17'd0; a1 <= 17'd0; a2 <= 17'd0; a3 <= 17'd0;
            a4 <= 17'd0; a5 <= 17'd0; a6 <= 17'd0;
        end else begin
            a0 <= m0_r + m1_r;
            a1 <= m2_r + m3_r;
            a2 <= m4_r + m5_r;
            a3 <= m6_r + m7_r;
            a4 <= m8_r + m9_r;
            a5 <= m10_r + m11_r;
            a6 <= m12_r;
        end
    end
    
    // Second adder tree stage (4 additions)
    reg [17:0] b0, b1, b2, b3;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            b0 <= 18'd0; b1 <= 18'd0; b2 <= 18'd0; b3 <= 18'd0;
        end else begin
            b0 <= a0 + a1;
            b1 <= a2 + a3;
            b2 <= a4 + a5;
            b3 <= a6;
        end
    end
    
    // Third adder tree stage (2 additions)
    reg [18:0] c0, c1;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            c0 <= 19'd0; c1 <= 19'd0;
        end else begin
            c0 <= b0 + b1;
            c1 <= b2 + b3;
        end
    end
    
    // Final stage: one addition and output register
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            y <= 16'd0;
        end else begin
            y <= (c0 + c1);
        end
    end
    
    // Delay line update (shift register)
    integer i;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 26; i = i + 1)
                dly[i] <= 8'd0;
        end else begin
            dly[0] <= x;
            for (i = 1; i < 26; i = i + 1)
                dly[i] <= dly[i-1];
        end
    end
    
endmodule