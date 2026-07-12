module sft__fir18_8b__g8 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [7:0] a0, a1, a2, a3, a4, a5, a6, a7, a8, a9, a10, a11, a12, a13, a14, a15, a16, a17;
    wire [23:0] acc = 8'd3 * a0 + 8'd5 * a1 + 8'd7 * a2 + 8'd9 * a3 + 8'd11 * a4 + 8'd13 * a5 + 8'd15 * a6 + 8'd17 * a7 + 8'd19 * a8 + 8'd19 * a9 + 8'd17 * a10 + 8'd15 * a11 + 8'd13 * a12 + 8'd11 * a13 + 8'd9 * a14 + 8'd7 * a15 + 8'd5 * a16 + 8'd3 * a17;
    always @(posedge clk) begin
        if (!rst_n) begin
            a0 <= 8'd0; a1 <= 8'd0; a2 <= 8'd0; a3 <= 8'd0; a4 <= 8'd0; a5 <= 8'd0; a6 <= 8'd0; a7 <= 8'd0; a8 <= 8'd0; a9 <= 8'd0; a10 <= 8'd0; a11 <= 8'd0; a12 <= 8'd0; a13 <= 8'd0; a14 <= 8'd0; a15 <= 8'd0; a16 <= 8'd0; a17 <= 8'd0; y <= 16'd0;
        end else begin
            a0 <= x;
            a1 <= a0;
            a2 <= a1;
            a3 <= a2;
            a4 <= a3;
            a5 <= a4;
            a6 <= a5;
            a7 <= a6;
            a8 <= a7;
            a9 <= a8;
            a10 <= a9;
            a11 <= a10;
            a12 <= a11;
            a13 <= a12;
            a14 <= a13;
            a15 <= a14;
            a16 <= a15;
            a17 <= a16;
            y <= acc[15:0];
        end
    end
endmodule