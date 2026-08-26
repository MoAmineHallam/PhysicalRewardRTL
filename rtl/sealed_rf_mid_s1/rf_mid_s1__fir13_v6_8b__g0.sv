module rf_mid_s1__fir13_v6_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [23:0] a0, a1, a2, a3, a4, a5, a6, a7, a8, a9, a10, a11, a12;
    always @(posedge clk) begin
        if (!rst_n) begin
            a0 <= 24'd0; a1 <= 24'd0; a2 <= 24'd0; a3 <= 24'd0; a4 <= 24'd0; a5 <= 24'd0; a6 <= 24'd0; a7 <= 24'd0; a8 <= 24'd0; a9 <= 24'd0; a10 <= 24'd0; a11 <= 24'd0; a12 <= 24'd0; y <= 16'd0;
        end else begin
            a0 <= 8'd19 * x + a1;
            a1 <= 8'd28 * x + a2;
            a2 <= 8'd42 * x + a3;
            a3 <= 8'd41 * x + a4;
            a4 <= 8'd60 * x + a5;
            a5 <= 8'd8 * x + a6;
            a6 <= 8'd17 * x + a7;
            a7 <= 8'd9 * x + a8;
            a8 <= 8'd28 * x + a9;
            a9 <= 8'd42 * x + a10;
            a10 <= 8'd19 * x + a11;
            a11 <= 8'd44 * x + a12;
            a12 <= 8'd37 * x;
            y <= a0[15:0];
        end
    end
endmodule
