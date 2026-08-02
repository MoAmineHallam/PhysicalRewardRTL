module grpo__fir26_8b__g13 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [23:0] a0, a1, a2, a3, a4, a5, a6, a7, a8, a9, a10, a11, a12, a13, a14, a15, a16, a17, a18, a19, a20, a21, a22, a23, a24, a25;
    always @(posedge clk) begin
        if (!rst_n) begin
            a0 <= 24;
            a1 <= 0;
            a2 <= 0;
            a3 <= 0;
            a4 <= 0;
            a5 <= 0;
            a6 <= 0;
            a7 <= 0;
            a8 <= 0;
            a9 <= 0;
            a10 <= 0;
            a11 <= 0;
            a12 <= 0;
            a13 <= 0;
            a14 <= 0;
            a15 <= 0;
            a16 <= 0;
            a17 <= 0;
            a18 <= 0;
            a19 <= 0;
            a20 <= 0;
            a21 <= 0;
            a22 <= 0;
            a23 <= 0;
            a24 <= 0;
            a25 <= 0;
            y <= 0;
        end else begin
            a0 <= 3*x + a1;
            a1 <= 5*x + a2;
            a2 <= 7*x + a3;
            a3 <= 9*x + a4;
            a4 <= 11*x + a5;
            a5 <= 13*x + a6;
            a6 <= 15*x + a7;
            a7 <= 17*x + a8;
            a8 <= 19*x + a9;
            a9 <= 21*x + a10;
            a10 <= 23*x + a11;
            a11 <= 25*x + a12;
            a12 <= 27*x + a13;
            a13 <= 27*x + a14;
            a14 <= 25*x + a15;
            a15 <= 23*x + a16;
            a16 <= 21*x + a17;
            a17 <= 19*x + a18;
            a18 <= 17*x + a19;
            a19 <= 15*x + a20;
            a20 <= 13*x + a21;
            a21 <= 11*x + a22;
            a22 <= 9*x + a23;
            a23 <= 7*x + a24;
            a24 <= 5*x + a25;
            a25 <= 3*x;
            y <= a0[15:0];
        end
    end
endmodule