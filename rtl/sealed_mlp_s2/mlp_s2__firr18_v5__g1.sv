module mlp_s2__firr18_v5__g1 (
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
        end else begin
            a0 <= (2*1 + 3)*x + a1;
            a1 <= (2*2 + 3)*x + a2;
            a2 <= (2*3 + 3)*x + a3;
            a3 <= (2*4 + 3)*x + a4;
            a4 <= (2*5 + 3)*x + a5;
            a5 <= (2*6 + 3)*x + a6;
            a6 <= (2*7 + 3)*x + a7;
            a7 <= (2*8 + 3)*x + a8;
            a8 <= (2*9 + 3)*x + a9;
            a9 <= (2*10 + 3)*x + a10;
            a10 <= (2*11 + 3)*x + a11;
            a11 <= (2*12 + 3)*x + a12;
            a12 <= (2*13 + 3)*x + a13;
            a13 <= (2*14 + 3)*x + a14;
            a14 <= (2*15 + 3)*x + a15;
            a15 <= (2*16 + 3)*x + a16;
            a16 <= (2*17 + 3)*x + a17;
            a17 <= (2*18 + 3)*x;
        end
    end
    assign y = a0[15:0];
endmodule
