module grpo__fir26_8b__g8 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [23:0] a0_reg;
    reg [23:0] a1_reg;
    reg [23:0] a2_reg;
    reg [23:0] a3_reg;
    reg [23:0] a4_reg;
    reg [23:0] a5_reg;
    reg [23:0] a6_reg;
    reg [23:0] a7_reg;
    reg [23:0] a8_reg;
    reg [23:0] a9_reg;
    reg [23:0] a10_reg;
    reg [23:0] a11_reg;
    reg [23:0] a12_reg;
    reg [23:0] a13_reg;
    reg [23:0] a14_reg;
    reg [23:0] a15_reg;
    reg [23:0] a16_reg;
    reg [23:0] a17_reg;
    reg [23:0] a18_reg;
    reg [23:0] a19_reg;
    reg [23:0] a20_reg;
    reg [23:0] a21_reg;
    reg [23:0] a22_reg;
    reg [23:0] a23_reg;
    reg [23:0] a24_reg;
    reg [23:0] a25_reg;
    always @(posedge clk) begin
        if (!rst_n) begin
            a0_reg <= 24'b0;
            a1_reg <= 24'b0;
            a2_reg <= 24'b0;
            a3_reg <= 24'b0;
            a4_reg <= 24'b0;
            a5_reg <= 24'b0;
            a6_reg <= 24'b0;
            a7_reg <= 24'b0;
            a8_reg <= 24'b0;
            a9_reg <= 24'b0;
            a10_reg <= 24'b0;
            a11_reg <= 24'b0;
            a12_reg <= 24'b0;
            a13_reg <= 24'b0;
            a14_reg <= 24'b0;
            a15_reg <= 24'b0;
            a16_reg <= 24'b0;
            a17_reg <= 24'b0;
            a18_reg <= 24'b0;
            a19_reg <= 24'b0;
            a20_reg <= 24'b0;
            a21_reg <= 24'b0;
            a22_reg <= 24'b0;
            a23_reg <= 24'b0;
            a24_reg <= 24'b0;
            a25_reg <= 24'b0;
            y <= 16'b0;
        end else begin
            a0_reg <= 8'd3 * x + a1_reg;
            a1_reg <= 8'd5 * x + a2_reg;
            a2_reg <= 8'd7 * x + a3_reg;
            a3_reg <= 8'd9 * x + a4_reg;
            a4_reg <= 8'd11 * x + a5_reg;
            a5_reg <= 8'd13 * x + a6_reg;
            a6_reg <= 8'd15 * x + a7_reg;
            a7_reg <= 8'd17 * x + a8_reg;
            a8_reg <= 8'd19 * x + a9_reg;
            a9_reg <= 8'd21 * x + a10_reg;
            a10_reg <= 8'd23 * x + a11_reg;
            a11_reg <= 8'd25 * x + a12_reg;
            a12_reg <= 8'd27 * x + a13_reg;
            a13_reg <= 8'd27 * x + a14_reg;
            a14_reg <= 8'd25 * x + a15_reg;
            a15_reg <= 8'd23 * x + a16_reg;
            a16_reg <= 8'd21 * x + a17_reg;
            a17_reg <= 8'd19 * x + a18_reg;
            a18_reg <= 8'd17 * x + a19_reg;
            a19_reg <= 8'd15 * x + a20_reg;
            a20_reg <= 8'd13 * x + a21_reg;
            a21_reg <= 8'd11 * x + a22_reg;
            a22_reg <= 8'd9 * x + a23_reg;
            a23_reg <= 8'd7 * x + a24_reg;
            a24_reg <= 8'd5 * x + a25_reg;
            a25_reg <= 8'd3 * x;
            y <= a0_reg[15:0];
        end
    end
endmodule