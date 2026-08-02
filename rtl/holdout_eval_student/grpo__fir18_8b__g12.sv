module grpo__fir18_8b__g12 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [23:0] a0, a1, a2, a3, a4, a5, a6, a7, a8, a9, a10, a11, a12, a13, a14, a15, a16, a17;
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
            a16 <= 24'd0;
            a17 <= 24'd0;
            y <= 16'd0;
        end else begin
            a0 <= (3 * x) + a1;
            a1 <= (5 * x) + a2;
            a2 <= (7 * x) + a3;
            a3 <= (9 * x) + a4;
            a4 <= (11 * x) + a5;
            a5 <= (13 * x) + a6;
            a6 <= (15 * x) + a7;
            a7 <= (17 * x) + a8;
            a8 <= (19 * x) + a9;
            a9 <= (19 * x) + a10;
            a10 <= (17 * x) + a11;
            a11 <= (15 * x) + a12;
            a12 <= (13 * x) + a13;
            a13 <= (11 * x) + a14;
            a14 <= (9 * x) + a15;
            a15 <= (7 * x) + a16;
            a16 <= (5 * x) + a17;
            a17 <= (3 * x);
            y <= a0[15:0];
        end
    end
endmodule