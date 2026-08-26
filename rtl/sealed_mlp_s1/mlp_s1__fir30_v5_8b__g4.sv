module mlp_s1__fir30_v5_8b__g4 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [23:0] a0, a1, a2, a3, a4, a5, a6, a7, a8, a9, a10, a11, a12, a13, a14, a15, a16, a17, a18, a19, a20, a21, a22, a23, a24, a25, a26, a27, a28, a29;
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
            a18 <= 24'd0;
            a19 <= 24'd0;
            a20 <= 24'd0;
            a21 <= 24'd0;
            a22 <= 24'd0;
            a23 <= 24'd0;
            a24 <= 24'd0;
            a25 <= 24'd0;
            a26 <= 24'd0;
            a27 <= 24'd0;
            a28 <= 24'd0;
            a29 <= 24'd0;
        end else begin
            a0 <= 44 * x + a1;
            a1 <= 37 * x + a2;
            a2 <= 25 * x + a3;
            a3 <= 24 * x + a4;
            a4 <= 58 * x + a5;
            a5 <= 4 * x + a6;
            a6 <= 24 * x + a7;
            a7 <= 58 * x + a8;
            a8 <= 23 * x + a9;
            a9 <= 46 * x + a10;
            a10 <= 25 * x + a11;
            a11 <= 35 * x + a12;
            a12 <= 40 * x + a13;
            a13 <= 8 * x + a14;
            a14 <= 33 * x + a15;
            a15 <= 12 * x + a16;
            a16 <= 18 * x + a17;
            a17 <= 9 * x + a18;
            a18 <= 63 * x + a19;
            a19 <= 4 * x + a20;
            a20 <= 1 * x + a21;
            a21 <= 45 * x + a22;
            a22 <= 21 * x + a23;
            a23 <= 43 * x + a24;
            a24 <= 25 * x + a25;
            a25 <= 33 * x + a26;
            a26 <= 4 * x + a27;
            a27 <= 57 * x + a28;
            a28 <= 44 * x + a29;
            a29 <= 11 * x;
        end
    end
    always @(posedge clk) begin
        if (!rst_n) begin
            y <= 16'd0;
        end else begin
            y <= a0[15:0];
        end
    end
endmodule
