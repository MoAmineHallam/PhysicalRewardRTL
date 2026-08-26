module mlp_s2__fir30_v5_8b__g1 (
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
            a0 <= 8'd44 * x + a1;
            a1 <= 8'd37 * x + a2;
            a2 <= 8'd25 * x + a3;
            a3 <= 8'd24 * x + a4;
            a4 <= 8'd58 * x + a5;
            a5 <= 8'd4 * x + a6;
            a6 <= 8'd24 * x + a7;
            a7 <= 8'd58 * x + a8;
            a8 <= 8'd23 * x + a9;
            a9 <= 8'd46 * x + a10;
            a10 <= 8'd25 * x + a11;
            a11 <= 8'd35 * x + a12;
            a12 <= 8'd40 * x + a13;
            a13 <= 8'd8 * x + a14;
            a14 <= 8'd33 * x + a15;
            a15 <= 8'd12 * x + a16;
            a16 <= 8'd18 * x + a17;
            a17 <= 8'd9 * x + a18;
            a18 <= 8'd63 * x + a19;
            a19 <= 8'd4 * x + a20;
            a20 <= 8'd1 * x + a21;
            a21 <= 8'd45 * x + a22;
            a22 <= 8'd21 * x + a23;
            a23 <= 8'd43 * x + a24;
            a24 <= 8'd25 * x + a25;
            a25 <= 8'd33 * x + a26;
            a26 <= 8'd4 * x + a27;
            a27 <= 8'd57 * x + a28;
            a28 <= 8'd44 * x + a29;
            a29 <= 8'd11 * x;
        end
    end
    assign y = a0[15:0];
endmodule
