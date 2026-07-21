module apifast__firr40__g6 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Delay line - 40 taps (tap 0 = newest)
    reg [7:0] delay_line [0:39];
    
    // Pipeline stages for the adder tree
    // Stage 1: multiply and first level of addition (pairs)
    // Stage 2-5: adder tree reduction
    // Final stage: output register
    
    // First pipeline stage registers - results of multiply-add pairs
    reg [15:0] stage1 [0:19];  // 20 results from 20 pairs
    
    // Intermediate pipeline stages
    reg [15:0] stage2 [0:9];   // 10 results
    reg [15:0] stage3 [0:4];   // 5 results
    reg [15:0] stage4 [0:2];   // 3 results
    reg [15:0] stage5 [0:1];   // 2 results
    reg [15:0] stage6;         // 1 final result
    
    // Delay line shift and input
    integer i;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 40; i = i + 1)
                delay_line[i] <= 8'd0;
        end else begin
            // Shift delay line and insert new sample
            for (i = 39; i > 0; i = i - 1)
                delay_line[i] <= delay_line[i-1];
            delay_line[0] <= x;
        end
    end
    
    // Pipeline Stage 1: Multiply each tap by coefficient (k+1) and add in pairs
    // Coefficients: tap0*1, tap1*2, tap2*3, ..., tap39*40
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 20; i = i + 1)
                stage1[i] <= 16'd0;
        end else begin
            // Pair 0: tap0*1 + tap1*2
            stage1[0] <= ({8'd0, delay_line[0]} * 16'd1) + ({8'd0, delay_line[1]} * 16'd2);
            // Pair 1: tap2*3 + tap3*4
            stage1[1] <= ({8'd0, delay_line[2]} * 16'd3) + ({8'd0, delay_line[3]} * 16'd4);
            // Pair 2: tap4*5 + tap5*6
            stage1[2] <= ({8'd0, delay_line[4]} * 16'd5) + ({8'd0, delay_line[5]} * 16'd6);
            // Pair 3: tap6*7 + tap7*8
            stage1[3] <= ({8'd0, delay_line[6]} * 16'd7) + ({8'd0, delay_line[7]} * 16'd8);
            // Pair 4: tap8*9 + tap9*10
            stage1[4] <= ({8'd0, delay_line[8]} * 16'd9) + ({8'd0, delay_line[9]} * 16'd10);
            // Pair 5: tap10*11 + tap11*12
            stage1[5] <= ({8'd0, delay_line[10]} * 16'd11) + ({8'd0, delay_line[11]} * 16'd12);
            // Pair 6: tap12*13 + tap13*14
            stage1[6] <= ({8'd0, delay_line[12]} * 16'd13) + ({8'd0, delay_line[13]} * 16'd14);
            // Pair 7: tap14*15 + tap15*16
            stage1[7] <= ({8'd0, delay_line[14]} * 16'd15) + ({8'd0, delay_line[15]} * 16'd16);
            // Pair 8: tap16*17 + tap17*18
            stage1[8] <= ({8'd0, delay_line[16]} * 16'd17) + ({8'd0, delay_line[17]} * 16'd18);
            // Pair 9: tap18*19 + tap19*20
            stage1[9] <= ({8'd0, delay_line[18]} * 16'd19) + ({8'd0, delay_line[19]} * 16'd20);
            // Pair 10: tap20*21 + tap21*22
            stage1[10] <= ({8'd0, delay_line[20]} * 16'd21) + ({8'd0, delay_line[21]} * 16'd22);
            // Pair 11: tap22*23 + tap23*24
            stage1[11] <= ({8'd0, delay_line[22]} * 16'd23) + ({8'd0, delay_line[23]} * 16'd24);
            // Pair 12: tap24*25 + tap25*26
            stage1[12] <= ({8'd0, delay_line[24]} * 16'd25) + ({8'd0, delay_line[25]} * 16'd26);
            // Pair 13: tap26*27 + tap27*28
            stage1[13] <= ({8'd0, delay_line[26]} * 16'd27) + ({8'd0, delay_line[27]} * 16'd28);
            // Pair 14: tap28*29 + tap29*30
            stage1[14] <= ({8'd0, delay_line[28]} * 16'd29) + ({8'd0, delay_line[29]} * 16'd30);
            // Pair 15: tap30*31 + tap31*32
            stage1[15] <= ({8'd0, delay_line[30]} * 16'd31) + ({8'd0, delay_line[31]} * 16'd32);
            // Pair 16: tap32*33 + tap33*34
            stage1[16] <= ({8'd0, delay_line[32]} * 16'd33) + ({8'd0, delay_line[33]} * 16'd34);
            // Pair 17: tap34*35 + tap35*36
            stage1[17] <= ({8'd0, delay_line[34]} * 16'd35) + ({8'd0, delay_line[35]} * 16'd36);
            // Pair 18: tap36*37 + tap37*38
            stage1[18] <= ({8'd0, delay_line[36]} * 16'd37) + ({8'd0, delay_line[37]} * 16'd38);
            // Pair 19: tap38*39 + tap39*40
            stage1[19] <= ({8'd0, delay_line[38]} * 16'd39) + ({8'd0, delay_line[39]} * 16'd40);
        end
    end
    
    // Pipeline Stage 2: Add pairs together (20 -> 10)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 10; i = i + 1)
                stage2[i] <= 16'd0;
        end else begin
            stage2[0] <= stage1[0] + stage1[1];
            stage2[1] <= stage1[2] + stage1[3];
            stage2[2] <= stage1[4] + stage1[5];
            stage2[3] <= stage1[6] + stage1[7];
            stage2[4] <= stage1[8] + stage1[9];
            stage2[5] <= stage1[10] + stage1[11];
            stage2[6] <= stage1[12] + stage1[13];
            stage2[7] <= stage1[14] + stage1[15];
            stage2[8] <= stage1[16] + stage1[17];
            stage2[9] <= stage1[18] + stage1[19];
        end
    end
    
    // Pipeline Stage 3: Add to reduce (10 -> 5)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 5; i = i + 1)
                stage3[i] <= 16'd0;
        end else begin
            stage3[0] <= stage2[0] + stage2[1];
            stage3[1] <= stage2[2] + stage2[3];
            stage3[2] <= stage2[4] + stage2[5];
            stage3[3] <= stage2[6] + stage2[7];
            stage3[4] <= stage2[8] + stage2[9];
        end
    end
    
    // Pipeline Stage 4: Add to reduce (5 -> 3)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 3; i = i + 1)
                stage4[i] <= 16'd0;
        end else begin
            stage4[0] <= stage3[0] + stage3[1];
            stage4[1] <= stage3[2] + stage3[3];
            stage4[2] <= stage3[4];  // Pass through
        end
    end
    
    // Pipeline Stage 5: Add to reduce (3 -> 2)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 2; i = i + 1)
                stage5[i] <= 16'd0;
        end else begin
            stage5[0] <= stage4[0] + stage4[1];
            stage5[1] <= stage4[2];  // Pass through
        end
    end
    
    // Pipeline Stage 6: Final reduction (2 -> 1)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            stage6 <= 16'd0;
        end else begin
            stage6 <= stage5[0] + stage5[1];
        end
    end
    
    // Output register
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            y <= 16'd0;
        else
            y <= stage6;
    end

endmodule