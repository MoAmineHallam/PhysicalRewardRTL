module mlp_s2__fir13_v6_8b__g5 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [23:0] a0, a1, a2, a3, a4, a5, a6, a7, a8, a9, a10, a11, a12;
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
            y <= 16'd0;
        end else begin
            a0 <= x * 24'd19 + a1;
            a1 <= x * 24'd28 + a2;
            a2 <= x * 24'd42 + a3;
            a3 <= x * 24'd41 + a4;
            a4 <= x * 24'd60 + a5;
            a5 <= x * 24'd8 + a6;
            a6 <= x * 24'd17 + a7;
            a7 <= x * 24'd9 + a8;
            a8 <= x * 24'd28 + a9;
            a9 <= x * 24'd42 + a10;
            a10 <= x * 24'd19 + a11;
            a11 <= x * 24'd44 + a12;
            a12 <= x * 24'd37;
            y <= a0[15:0];
        end
    end
endmodule
