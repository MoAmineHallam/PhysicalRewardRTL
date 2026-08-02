module sft__fir26_8b__g2 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [25:0] a0, a1, a2, a3, a4, a5, a6, a7, a8, a9, a10, a11, a12, a13, a14, a15, a16, a17, a18, a19, a20, a21, a22, a23, a24, a25;
    always @(posedge clk) begin
        if (!rst_n) begin
            a0 <= 26'd0;
            a1 <= 26'd0;
            a2 <= 26'd0;
            a3 <= 26'd0;
            a4 <= 26'd0;
            a5 <= 26'd0;
            a6 <= 26'd0;
            a7 <= 26'd0;
            a8 <= 26'd0;
            a9 <= 26'd0;
            a10 <= 26'd0;
            a11 <= 26'd0;
            a12 <= 26'd0;
            a13 <= 26'd0;
            a14 <= 26'd0;
            a15 <= 26'd0;
            a16 <= 26'd0;
            a17 <= 26'd0;
            a18 <= 26'd0;
            a19 <= 26'd0;
            a20 <= 26'd0;
            a21 <= 26'd0;
            a22 <= 26'd0;
            a23 <= 26'd0;
            a24 <= 26'd0;
            a25 <= 26'd0;
        y <= 16'd0;
        end else begin
            a0 <= 8'd3 * x + a1;
            a1 <= 8'd5 * x + a2;
            a2 <= 8'd7 * x + a3;
            a3 <= 8'd9 * x + a4;
            a4 <= 8'd11 * x + a5;
            a5 <= 8'd13 * x + a6;
            a6 <= 8'd15 * x + a7;
            a7 <= 8'd17 * x + a8;
            a8 <= 8'd19 * x + a9;
            a9 <= 8'd21 * x + a10;
            a10 <= 8'd23 * x + a11;
            a11 <= 8'd25 * x + a12;
            a12 <= 8'd27 * x + a13;
            a13 <= 8'd27 * x + a14;
            a14 <= 8'd25 * x + a15;
            a15 <= 8'd23 * x + a16;
            a16 <= 8'd21 * x + a17;
            a17 <= 8'd19 * x + a18;
            a18 <= 8'd17 * x + a19;
            a19 <= 8'd15 * x + a20;
            a20 <= 8'd13 * x + a21;
            a21 <= 8'd11 * x + a22;
            a22 <= 8'd9 * x + a23;
            a23 <= 8'd7 * x + a24;
            a24 <= 8'd5 * x + a25;
            a25 <= 8'd3 * x;
            y <= a0[15:0];
        end
    end
endmodule