module apifast__fir10_8b__g2 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Coefficients
    localparam [7:0] c0 = 8'd3;
    localparam [7:0] c1 = 8'd5;
    localparam [7:0] c2 = 8'd7;
    localparam [7:0] c3 = 8'd9;
    localparam [7:0] c4 = 8'd11;
    localparam [7:0] c5 = 8'd11;
    localparam [7:0] c6 = 8'd9;
    localparam [7:0] c7 = 8'd7;
    localparam [7:0] c8 = 8'd5;
    localparam [7:0] c9 = 8'd3;

    // Delay line (shift register)
    reg [7:0] d0, d1, d2, d3, d4, d5, d6, d7, d8, d9;
    
    // Pipeline registers for partial sums
    reg [15:0] p0, p1, p2, p3, p4; // 5 stages of tree adder
    
    // Intermediate product registers
    reg [15:0] m0, m1, m2, m3, m4, m5, m6, m7, m8, m9;

    // Shift register logic (registered)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            d0 <= 8'd0;
            d1 <= 8'd0;
            d2 <= 8'd0;
            d3 <= 8'd0;
            d4 <= 8'd0;
            d5 <= 8'd0;
            d6 <= 8'd0;
            d7 <= 8'd0;
            d8 <= 8'd0;
            d9 <= 8'd0;
        end else begin
            d0 <= x;
            d1 <= d0;
            d2 <= d1;
            d3 <= d2;
            d4 <= d3;
            d5 <= d4;
            d6 <= d5;
            d7 <= d6;
            d8 <= d7;
            d9 <= d8;
        end
    end

    // Stage 1: Multiplications (registered)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            m0 <= 16'd0; m1 <= 16'd0; m2 <= 16'd0; m3 <= 16'd0; m4 <= 16'd0;
            m5 <= 16'd0; m6 <= 16'd0; m7 <= 16'd0; m8 <= 16'd0; m9 <= 16'd0;
        end else begin
            m0 <= d0 * c0;
            m1 <= d1 * c1;
            m2 <= d2 * c2;
            m3 <= d3 * c3;
            m4 <= d4 * c4;
            m5 <= d5 * c5;
            m6 <= d6 * c6;
            m7 <= d7 * c7;
            m8 <= d8 * c8;
            m9 <= d9 * c9;
        end
    end

    // Stage 2: First partial sums (5 groups of 2)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            p0 <= 16'd0; p1 <= 16'd0; p2 <= 16'd0; p3 <= 16'd0; p4 <= 16'd0;
        end else begin
            p0 <= m0 + m1;
            p1 <= m2 + m3;
            p2 <= m4 + m5;
            p3 <= m6 + m7;
            p4 <= m8 + m9;
        end
    end

    // Stage 3: Second partial sums (2 groups: p0+p1, p2+p3, plus p4)
    reg [15:0] q0, q1, q2;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            q0 <= 16'd0; q1 <= 16'd0; q2 <= 16'd0;
        end else begin
            q0 <= p0 + p1;
            q1 <= p2 + p3;
            q2 <= p4;
        end
    end

    // Stage 4: Final sum
    reg [15:0] sum_stage;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sum_stage <= 16'd0;
        end else begin
            sum_stage <= q0 + q1 + q2;
        end
    end

    // Stage 5: Output registered (low 16 bits)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            y <= 16'd0;
        end else begin
            y <= sum_stage[15:0];
        end
    end

endmodule