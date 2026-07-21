module apifast__fir18_8b__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Delay line (registered)
    reg [7:0] delay_line [0:17];
    
    // Pipeline registers for intermediate products and sums
    // Stage 1: Products
    reg [15:0] p0, p1, p2, p3, p4, p5, p6, p7, p8;
    reg [15:0] p9, p10, p11, p12, p13, p14, p15, p16, p17;
    
    // Stage 2-5: Partial sums (tree adder structure)
    reg [15:0] s1_0, s1_1, s1_2, s1_3, s1_4, s1_5, s1_6, s1_7, s1_8;
    reg [15:0] s2_0, s2_1, s2_2, s2_3, s2_4;
    reg [15:0] s3_0, s3_1, s3_2;
    reg [15:0] s4_0, s4_1;
    reg [15:0] s5_0;
    
    integer i;
    
    // Coefficients
    localparam [7:0] c0  = 8'd3;
    localparam [7:0] c1  = 8'd5;
    localparam [7:0] c2  = 8'd7;
    localparam [7:0] c3  = 8'd9;
    localparam [7:0] c4  = 8'd11;
    localparam [7:0] c5  = 8'd13;
    localparam [7:0] c6  = 8'd15;
    localparam [7:0] c7  = 8'd17;
    localparam [7:0] c8  = 8'd19;
    localparam [7:0] c9  = 8'd19;
    localparam [7:0] c10 = 8'd17;
    localparam [7:0] c11 = 8'd15;
    localparam [7:0] c12 = 8'd13;
    localparam [7:0] c13 = 8'd11;
    localparam [7:0] c14 = 8'd9;
    localparam [7:0] c15 = 8'd7;
    localparam [7:0] c16 = 8'd5;
    localparam [7:0] c17 = 8'd3;
    
    // Delay line update and reset
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 18; i = i + 1)
                delay_line[i] <= 8'd0;
        end else begin
            delay_line[0] <= x;
            for (i = 1; i < 18; i = i + 1)
                delay_line[i] <= delay_line[i-1];
        end
    end
    
    // Pipeline Stage 1: Multiply
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            p0  <= 16'd0; p1  <= 16'd0; p2  <= 16'd0; p3  <= 16'd0;
            p4  <= 16'd0; p5  <= 16'd0; p6  <= 16'd0; p7  <= 16'd0;
            p8  <= 16'd0; p9  <= 16'd0; p10 <= 16'd0; p11 <= 16'd0;
            p12 <= 16'd0; p13 <= 16'd0; p14 <= 16'd0; p15 <= 16'd0;
            p16 <= 16'd0; p17 <= 16'd0;
        end else begin
            p0  <= delay_line[0]  * c0;
            p1  <= delay_line[1]  * c1;
            p2  <= delay_line[2]  * c2;
            p3  <= delay_line[3]  * c3;
            p4  <= delay_line[4]  * c4;
            p5  <= delay_line[5]  * c5;
            p6  <= delay_line[6]  * c6;
            p7  <= delay_line[7]  * c7;
            p8  <= delay_line[8]  * c8;
            p9  <= delay_line[9]  * c9;
            p10 <= delay_line[10] * c10;
            p11 <= delay_line[11] * c11;
            p12 <= delay_line[12] * c12;
            p13 <= delay_line[13] * c13;
            p14 <= delay_line[14] * c14;
            p15 <= delay_line[15] * c15;
            p16 <= delay_line[16] * c16;
            p17 <= delay_line[17] * c17;
        end
    end
    
    // Pipeline Stage 2: First level of addition tree (9 additions)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            s1_0 <= 16'd0; s1_1 <= 16'd0; s1_2 <= 16'd0; s1_3 <= 16'd0;
            s1_4 <= 16'd0; s1_5 <= 16'd0; s1_6 <= 16'd0; s1_7 <= 16'd0;
            s1_8 <= 16'd0;
        end else begin
            s1_0 <= p0  + p1;
            s1_1 <= p2  + p3;
            s1_2 <= p4  + p5;
            s1_3 <= p6  + p7;
            s1_4 <= p8  + p9;
            s1_5 <= p10 + p11;
            s1_6 <= p12 + p13;
            s1_7 <= p14 + p15;
            s1_8 <= p16 + p17;
        end
    end
    
    // Pipeline Stage 3: Second level (5 additions)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            s2_0 <= 16'd0; s2_1 <= 16'd0; s2_2 <= 16'd0; s2_3 <= 16'd0;
            s2_4 <= 16'd0;
        end else begin
            s2_0 <= s1_0 + s1_1;
            s2_1 <= s1_2 + s1_3;
            s2_2 <= s1_4 + s1_5;
            s2_3 <= s1_6 + s1_7;
            s2_4 <= s1_8;
        end
    end
    
    // Pipeline Stage 4: Third level (3 additions)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            s3_0 <= 16'd0; s3_1 <= 16'd0; s3_2 <= 16'd0;
        end else begin
            s3_0 <= s2_0 + s2_1;
            s3_1 <= s2_2 + s2_3;
            s3_2 <= s2_4;
        end
    end
    
    // Pipeline Stage 5: Fourth level (2 additions)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            s4_0 <= 16'd0; s4_1 <= 16'd0;
        end else begin
            s4_0 <= s3_0 + s3_1;
            s4_1 <= s3_2;
        end
    end
    
    // Pipeline Stage 6: Final addition and output (1 addition)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            s5_0 <= 16'd0;
            y    <= 16'd0;
        end else begin
            s5_0 <= s4_0 + s4_1;
            y    <= s5_0;
        end
    end

endmodule