module apifast__fir10_8b__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Fixed coefficients
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

    // Delay line registers
    reg [7:0] d0, d1, d2, d3, d4, d5, d6, d7, d8, d9;

    // Pipeline registers for products and partial sums
    reg [15:0] p0, p1, p2, p3, p4, p5, p6, p7, p8, p9;
    reg [15:0] s0, s1, s2, s3, s4, s5, s6, s7, s8;

    // Stage 1: Shift delay line and compute products
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
            p0 <= 16'd0;
            p1 <= 16'd0;
            p2 <= 16'd0;
            p3 <= 16'd0;
            p4 <= 16'd0;
            p5 <= 16'd0;
            p6 <= 16'd0;
            p7 <= 16'd0;
            p8 <= 16'd0;
            p9 <= 16'd0;
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
            
            // Multiply each tap (pipeline stage 1)
            p0 <= d0 * c0;
            p1 <= d1 * c1;
            p2 <= d2 * c2;
            p3 <= d3 * c3;
            p4 <= d4 * c4;
            p5 <= d5 * c5;
            p6 <= d6 * c6;
            p7 <= d7 * c7;
            p8 <= d8 * c8;
            p9 <= d9 * c9;
        end
    end

    // Stage 2: First level of pairwise addition
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            s0 <= 16'd0;
            s1 <= 16'd0;
            s2 <= 16'd0;
            s3 <= 16'd0;
            s4 <= 16'd0;
            s5 <= 16'd0;
            s6 <= 16'd0;
            s7 <= 16'd0;
            s8 <= 16'd0;
        end else begin
            s0 <= p0 + p1;
            s1 <= p2 + p3;
            s2 <= p4 + p5;
            s3 <= p6 + p7;
            s4 <= p8 + p9;
            // These extra stages maintain pipeline balance
            s5 <= s0;
            s6 <= s1;
            s7 <= s2;
            s8 <= s3;
        end
    end

    // Stage 3: Second level of addition
    reg [15:0] t0, t1, t2, t3;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            t0 <= 16'd0;
            t1 <= 16'd0;
            t2 <= 16'd0;
            t3 <= 16'd0;
        end else begin
            t0 <= s0 + s1;  // (p0+p1)+(p2+p3)
            t1 <= s2 + s3;  // (p4+p5)+(p6+p7)
            t2 <= s4;       // (p8+p9) carry forward
            t3 <= t0;
        end
    end

    // Stage 4: Third level
    reg [15:0] u0, u1;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            u0 <= 16'd0;
            u1 <= 16'd0;
        end else begin
            u0 <= t0 + t1;  // ((p0+p1)+(p2+p3)) + ((p4+p5)+(p6+p7))
            u1 <= t2;       // (p8+p9)
        end
    end

    // Stage 5: Final addition and output
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            y <= 16'd0;
        end else begin
            y <= u0 + u1;   // Final sum -> low 16 bits
        end
    end

endmodule