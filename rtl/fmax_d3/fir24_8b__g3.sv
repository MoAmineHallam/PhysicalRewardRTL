module fir24_8b__g3 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [23:0] w0, w1, w2, w3, w4, w5, w6, w7, w8, w9, w10, w11, w12, w13, w14, w15, w16, w17, w18, w19, w20, w21, w22, w23;
    always @(posedge clk) begin
        if (!rst_n) begin
            w0 <= 24'd0;
            w1 <= 24'd0;
            w2 <= 24'd0;
            w3 <= 24'd0;
            w4 <= 24'd0;
            w5 <= 24'd0;
            w6 <= 24'd0;
            w7 <= 24'd0;
            w8 <= 24'd0;
            w9 <= 24'd0;
            w10 <= 24'd0;
            w11 <= 24'd0;
            w12 <= 24'd0;
            w13 <= 24'd0;
            w14 <= 24'd0;
            w15 <= 24'd0;
            w16 <= 24'd0;
            w17 <= 24'd0;
            w18 <= 24'd0;
            w19 <= 24'd0;
            w20 <= 24'd0;
            w21 <= 24'd0;
            w22 <= 24'd0;
            w23 <= 24'd0;
            y <= 16'd0;
        end else begin
            w0 <= 8'd3 * x + w1;
            w1 <= 8'd5 * x + w2;
            w2 <= 8'd7 * x + w3;
            w3 <= 8'd9 * x + w4;
            w4 <= 8'd11 * x + w5;
            w5 <= 8'd13 * x + w6;
            w6 <= 8'd15 * x + w7;
            w7 <= 8'd17 * x + w8;
            w8 <= 8'd19 * x + w9;
            w9 <= 8'd21 * x + w10;
            w10 <= 8'd23 * x + w11;
            w11 <= 8'd25 * x + w12;
            w12 <= 8'd25 * x + w13;
            w13 <= 8'd23 * x + w14;
            w14 <= 8'd21 * x + w15;
            w15 <= 8'd19 * x + w16;
            w16 <= 8'd17 * x + w17;
            w17 <= 8'd15 * x + w18;
            w18 <= 8'd13 * x + w19;
            w19 <= 8'd11 * x + w20;
            w20 <= 8'd9 * x + w21;
            w21 <= 8'd7 * x + w22;
            w22 <= 8'd5 * x + w23;
            w23 <= 8'd3 * x;
            y <= w0[15:0];
        end
    end
endmodule