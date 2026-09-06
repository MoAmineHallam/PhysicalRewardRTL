module rf_s3__fir42_v6_8b__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [23:0] a0, a1, a2, a3, a4, a5, a6, a7, a8, a9, a10, a11, a12, a13, a14, a15, a16, a17, a18, a19, a20, a21, a22, a23, a24, a25, a26, a27, a28, a29, a30, a31, a32, a33, a34, a35, a36, a37, a38, a39, a40, a41;
    always @(posedge clk) begin
        if (!rst_n) begin
            y <= 'd0; a0 <= 'd0; a1 <= 'd0; a2 <= 'd0; a3 <= 'd0; a4 <= 'd0; a5 <= 'd0; a6 <= 'd0; a7 <= 'd0; a8 <= 'd0; a9 <= 'd0; a10 <= 'd0; a11 <= 'd0; a12 <= 'd0; a13 <= 'd0; a14 <= 'd0; a15 <= 'd0; a16 <= 'd0; a17 <= 'd0; a18 <= 'd0; a19 <= 'd0; a20 <= 'd0; a21 <= 'd0; a22 <= 'd0; a23 <= 'd0; a24 <= 'd0; a25 <= 'd0; a26 <= 'd0; a27 <= 'd0; a28 <= 'd0; a29 <= 'd0; a30 <= 'd0; a31 <= 'd0; a32 <= 'd0; a33 <= 'd0; a34 <= 'd0; a35 <= 'd0; a36 <= 'd0; a37 <= 'd0; a38 <= 'd0; a39 <= 'd0; a40 <= 'd0; a41 <= 'd0;
        end else begin
            a0 <= 8'd52 * x + a1;
            a1 <= 8'd37 * x + a2;
            a2 <= 8'd42 * x + a3;
            a3 <= 8'd47 * x + a4;
            a4 <= 8'd1 * x + a5;
            a5 <= 8'd38 * x + a6;
            a6 <= 8'd28 * x + a7;
            a7 <= 8'd58 * x + a8;
            a8 <= 8'd54 * x + a9;
            a9 <= 8'd41 * x + a10;
            a10 <= 8'd4 * x + a11;
            a11 <= 8'd12 * x + a12;
            a12 <= 8'd23 * x + a13;
            a13 <= 8'd32 * x + a14;
            a14 <= 8'd50 * x + a15;
            a15 <= 8'd48 * x + a16;
            a16 <= 8'd17 * x + a17;
            a17 <= 8'd27 * x + a18;
            a18 <= 8'd13 * x + a19;
            a19 <= 8'd16 * x + a20;
            a20 <= 8'd14 * x + a21;
            a21 <= 8'd50 * x + a22;
            a22 <= 8'd4 * x + a23;
            a23 <= 8'd29 * x + a24;
            a24 <= 8'd8 * x + a25;
            a25 <= 8'd63 * x + a26;
            a26 <= 8'd24 * x + a27;
            a27 <= 8'd30 * x + a28;
            a28 <= 8'd20 * x + a29;
            a29 <= 8'd53 * x + a30;
            a30 <= 8'd25 * x + a31;
            a31 <= 8'd18 * x + a32;
            a32 <= 8'd5 * x + a33;
            a33 <= 8'd54 * x + a34;
            a34 <= 8'd58 * x + a35;
            a35 <= 8'd1 * x + a36;
            a36 <= 8'd29 * x + a37;
            a37 <= 8'd23 * x + a38;
            a38 <= 8'd14 * x + a39;
            a39 <= 8'd28 * x + a40;
            a40 <= 8'd60 * x + a41;
            a41 <= 8'd9 * x;
            y <= a0[15:0];
        end
    end
endmodule
