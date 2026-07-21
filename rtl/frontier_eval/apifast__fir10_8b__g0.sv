module apifast__fir10_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Coefficients: [3, 5, 7, 9, 11, 11, 9, 7, 5, 3]
    // Pipeline stages to break the 10-product sum tree into single multiply-add per stage

    // Stage 0: Delay line and partial products
    reg [7:0] delay [0:9];      // 10-tap delay line
    wire [15:0] prod [0:9];     // 16-bit products (8b * 8b input = max 16b)

    // Product generation (purely combinational)
    assign prod[0] = delay[0] * 8'd3;
    assign prod[1] = delay[1] * 8'd5;
    assign prod[2] = delay[2] * 8'd7;
    assign prod[3] = delay[3] * 8'd9;
    assign prod[4] = delay[4] * 8'd11;
    assign prod[5] = delay[5] * 8'd11;
    assign prod[6] = delay[6] * 8'd9;
    assign prod[7] = delay[7] * 8'd7;
    assign prod[8] = delay[8] * 8'd5;
    assign prod[9] = delay[9] * 8'd3;

    // Pipeline registers for partial sums (5 pipeline stages for log2(10) ~ 4, extra stage for safety)
    reg [15:0] p0, p1, p2, p3, p4, p5, p6, p7, p8, p9; // first stage registers after multiply

    // Stage 1: Register products
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            p0 <= 16'd0; p1 <= 16'd0; p2 <= 16'd0; p3 <= 16'd0; p4 <= 16'd0;
            p5 <= 16'd0; p6 <= 16'd0; p7 <= 16'd0; p8 <= 16'd0; p9 <= 16'd0;
        end else begin
            p0 <= prod[0]; p1 <= prod[1]; p2 <= prod[2]; p3 <= prod[3]; p4 <= prod[4];
            p5 <= prod[5]; p6 <= prod[6]; p7 <= prod[7]; p8 <= prod[8]; p9 <= prod[9];
        end
    end

    // Stage 2: First level adders (5 pairs -> 5 results)
    reg [15:0] s2_0, s2_1, s2_2, s2_3, s2_4;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            s2_0 <= 16'd0; s2_1 <= 16'd0; s2_2 <= 16'd0; s2_3 <= 16'd0; s2_4 <= 16'd0;
        end else begin
            s2_0 <= p0 + p1;
            s2_1 <= p2 + p3;
            s2_2 <= p4 + p5;
            s2_3 <= p6 + p7;
            s2_4 <= p8 + p9;
        end
    end

    // Stage 3: Second level adders (2 pairs + leftover -> 3 results)
    reg [15:0] s3_0, s3_1, s3_2;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            s3_0 <= 16'd0; s3_1 <= 16'd0; s3_2 <= 16'd0;
        end else begin
            s3_0 <= s2_0 + s2_1;
            s3_1 <= s2_2 + s2_3;
            s3_2 <= s2_4;  // directly pass the odd one
        end
    end

    // Stage 4: Third level adders (1 pair + leftover -> 2 results)
    reg [15:0] s4_0, s4_1;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            s4_0 <= 16'd0; s4_1 <= 16'd0;
        end else begin
            s4_0 <= s3_0 + s3_1;
            s4_1 <= s3_2;
        end
    end

    // Stage 5: Final adder and output register
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            y <= 16'd0;
        end else begin
            y <= s4_0 + s4_1;
        end
    end

    // Delay line update (pipelined separately to keep x path short)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            delay[0] <= 8'd0;
            delay[1] <= 8'd0;
            delay[2] <= 8'd0;
            delay[3] <= 8'd0;
            delay[4] <= 8'd0;
            delay[5] <= 8'd0;
            delay[6] <= 8'd0;
            delay[7] <= 8'd0;
            delay[8] <= 8'd0;
            delay[9] <= 8'd0;
        end else begin
            delay[0] <= x;
            delay[1] <= delay[0];
            delay[2] <= delay[1];
            delay[3] <= delay[2];
            delay[4] <= delay[3];
            delay[5] <= delay[4];
            delay[6] <= delay[5];
            delay[7] <= delay[6];
            delay[8] <= delay[7];
            delay[9] <= delay[8];
        end
    end

endmodule