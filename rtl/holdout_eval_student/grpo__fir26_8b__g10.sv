module grpo__fir26_8b__g10 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [23:0] a0_l, a1_l, a2_l, a3_l, a4_l, a5_l, a6_l, a7_l, a8_l, a9_l, a10_l, a11_l, a12_l, a13_l, a14_l, a15_l, a16_l, a17_l, a18_l, a19_l, a20_l, a21_l, a22_l, a23_l, a24_l, a25_l;
    always @(posedge clk) begin
        if (!rst_n) begin
            a0_l <= 24'd0;
            a1_l <= 24'd0;
            a2_l <= 24'd0;
            a3_l <= 24'd0;
            a4_l <= 24'd0;
            a5_l <= 24'd0;
            a6_l <= 24'd0;
            a7_l <= 24'd0;
            a8_l <= 24'd0;
            a9_l <= 24'd0;
            a10_l <= 24'd0;
            a11_l <= 24'd0;
            a12_l <= 24'd0;
            a13_l <= 24'd0;
            a14_l <= 24'd0;
            a15_l <= 24'd0;
            a16_l <= 24'd0;
            a17_l <= 24'd0;
            a18_l <= 24'd0;
            a19_l <= 24'd0;
            a20_l <= 24'd0;
            a21_l <= 24'd0;
            a22_l <= 24'd0;
            a23_l <= 24'd0;
            a24_l <= 24'd0;
            a25_l <= 24'd0;
            y <= 16'd0;
        end else begin
            a0_l <= 8'd3 * x + a1_l;
            a1_l <= 8'd5 * x + a2_l;
            a2_l <= 8'd7 * x + a3_l;
            a3_l <= 8'd9 * x + a4_l;
            a4_l <= 8'd11 * x + a5_l;
            a5_l <= 8'd13 * x + a6_l;
            a6_l <= 8'd15 * x + a7_l;
            a7_l <= 8'd17 * x + a8_l;
            a8_l <= 8'd19 * x + a9_l;
            a9_l <= 8'd21 * x + a10_l;
            a10_l <= 8'd23 * x + a11_l;
            a11_l <= 8'd25 * x + a12_l;
            a12_l <= 8'd27 * x + a13_l;
            a13_l <= 8'd27 * x + a14_l;
            a14_l <= 8'd25 * x + a15_l;
            a15_l <= 8'd23 * x + a16_l;
            a16_l <= 8'd21 * x + a17_l;
            a17_l <= 8'd19 * x + a18_l;
            a18_l <= 8'd17 * x + a19_l;
            a19_l <= 8'd15 * x + a20_l;
            a20_l <= 8'd13 * x + a21_l;
            a21_l <= 8'd11 * x + a22_l;
            a22_l <= 8'd9 * x + a23_l;
            a23_l <= 8'd7 * x + a24_l;
            a24_l <= 8'd5 * x + a25_l;
            a25_l <= 8'd3 * x;
            y <= a0_l[15:0];
        end
    end
endmodule