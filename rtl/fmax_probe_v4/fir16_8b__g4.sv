module fir16_8b__g4 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [23:0] a0, a1, a2, a3, a4, a5, a6, a7, a8, a9, a10, a11, a12, a13, a14, a15;
    wire [23:0] m0, m1, m2, m3, m4, m5, m6, m7, m8, m9, m10, m11, m12, m13, m14, m15;
    assign m0 = 8'd3 * x;
    assign m1 = 8'd7 * x;
    assign m2 = 8'd12 * x;
    assign m3 = 8'd19 * x;
    assign m4 = 8'd27 * x;
    assign m5 = 8'd34 * x;
    assign m6 = 8'd40 * x;
    assign m7 = 8'd43 * x;
    assign m8 = 8'd43 * x;
    assign m9 = 8'd40 * x;
    assign m10 = 8'd34 * x;
    assign m11 = 8'd27 * x;
    assign m12 = 8'd19 * x;
    assign m13 = 8'd12 * x;
    assign m14 = 8'd7 * x;
    assign m15 = 8'd3 * x;
    always @(posedge clk) begin
        if (!rst_n) begin
            a0 <= 24'd0;
            a1 <= 24'd0;
            a2 <= 24'd0;
            a3 <= 24'd0;
            a4 <= 24'd0;
            a5 <= 24'd0;
            a6 <= 24'd0;
            a7 <= 24'd0;
            a8 <= 24'd0;
            a9 <= 24'd0;
            a10 <= 24'd0;
            a11 <= 24'd0;
            a12 <= 24'd0;
            a13 <= 24'd0;
            a14 <= 24'd0;
            a15 <= 24'd0;
            y <= 16'd0;
        end else begin
            a0 <= m0;
            a1 <= a0 + m1;
            a2 <= a1 + m2;
            a3 <= a2 + m3;
            a4 <= a3 + m4;
            a5 <= a4 + m5;
            a6 <= a5 + m6;
            a7 <= a6 + m7;
            a8 <= a7 + m8;
            a9 <= a8 + m9;
            a10 <= a9 + m10;
            a11 <= a10 + m11;
            a12 <= a11 + m12;
            a13 <= a12 + m13;
            a14 <= a13 + m14;
            a15 <= a14 + m15;
            y <= a15[15:0];
        end
    end
endmodule