module sft__fir18_8b__g6 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  d0, d1, d2, d3, d4, d5, d6, d7, d8, d9, d10, d11, d12, d13, d14, d15, d16, d17;
    reg  [15:0] p0, p1, p2, p3, p4, p5, p6, p7, p8, p9, p10, p11, p12, p13, p14, p15, p16, p17;
    always @(posedge clk) begin
        if (!rst_n) begin
            d0 <= 8'd0; d1 <= 8'd0; d2 <= 8'd0; d3 <= 8'd0; d4 <= 8'd0; d5 <= 8'd0; d6 <= 8'd0; d7 <= 8'd0; d8 <= 8'd0; d9 <= 8'd0; d10 <= 8'd0; d11 <= 8'd0; d12 <= 8'd0; d13 <= 8'd0; d14 <= 8'd0; d15 <= 8'd0; d16 <= 8'd0; d17 <= 8'd0; p0 <= 16'd0; p1 <= 16'd0; p2 <= 16'd0; p3 <= 16'd0; p4 <= 16'd0; p5 <= 16'd0; p6 <= 16'd0; p7 <= 16'd0; p8 <= 16'd0; p9 <= 16'd0; p10 <= 16'd0; p11 <= 16'd0; p12 <= 16'd0; p13 <= 16'd0; p14 <= 16'd0; p15 <= 16'd0; p16 <= 16'd0; p17 <= 16'd0; y <= 16'd0;
        end else begin
            d0 <= x;
            p0 <= 8'd3 * d0;
            d1 <= d0;
            p1 <= 8'd5 * d1;
            d2 <= d1;
            p2 <= 8'd7 * d2;
            d3 <= d2;
            p3 <= 8'd9 * d3;
            d4 <= d3;
            p4 <= 8'd11 * d4;
            d5 <= d4;
            p5 <= 8'd13 * d5;
            d6 <= d5;
            p6 <= 8'd15 * d6;
            d7 <= d6;
            p7 <= 8'd17 * d7;
            d8 <= d7;
            p8 <= 8'd19 * d8;
            d9 <= d8;
            p9 <= 8'd19 * d9;
            d10 <= d9;
            p10 <= 8'd17 * d10;
            d11 <= d10;
            p11 <= 8'd15 * d11;
            d12 <= d11;
            p12 <= 8'd13 * d12;
            d13 <= d12;
            p13 <= 8'd11 * d13;
            d14 <= d13;
            p14 <= 8'd9 * d14;
            d15 <= d14;
            p15 <= 8'd7 * d15;
            d16 <= d15;
            p16 <= 8'd5 * d16;
            d17 <= d16;
            p17 <= 8'd3 * d17;
            y <= p0 + p1 + p2 + p3 + p4 + p5 + p6 + p7 + p8 + p9 + p10 + p11 + p12 + p13 + p14 + p15 + p16 + p17;
        end
    end
endmodule