module sft__fir18_8b__g6 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [23:0] a0, a1, a2, a3, a4, a5, a6, a7, a8, a9, a10, a11, a12, a13, a14, a15, a16, a17;
    always @(posedge clk) begin
        if (!rst_n) begin
            a0 <= 24'd0; a1 <= 24'd0; a2 <= 24'd0; a3 <= 24'd0; a4 <= 24'd0; a5 <= 24'd0; a6 <= 24'd0; a7 <= 24'd0; a8 <= 24'd0; a9 <= 24'd0; a10 <= 24'd0; a11 <= 24'd0; a12 <= 24'd0; a13 <= 24'd0; a14 <= 24'd0; a15 <= 24'd0; a16 <= 24'd0; a17 <= 24'd0; y <= 16'd0;
        end else begin
            a0 <= x * 8'd3 + a1;
            a1 <= x * 8'd5 + a2;
            a2 <= x * 8'd7 + a3;
            a3 <= x * 8'd9 + a4;
            a4 <= x * 8'd11 + a5;
            a5 <= x * 8'd13 + a6;
            a6 <= x * 8'd15 + a7;
            a7 <= x * 8'd17 + a8;
            a8 <= x * 8'd19 + a9;
            a9 <= x * 8'd19 + a10;
            a10 <= x * 8'd17 + a11;
            a11 <= x * 8'd15 + a12;
            a12 <= x * 8'd13 + a13;
            a13 <= x * 8'd11 + a14;
            a14 <= x * 8'd9 + a15;
            a15 <= x * 8'd7 + a16;
            a16 <= x * 8'd5 + a17;
            a17 <= x * 8'd3;
            y <= a0[15:0];
        end
    end
endmodule