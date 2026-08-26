module sft__fir30_v5_8b__g7 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  d0, d1, d2, d3, d4, d5, d6, d7, d8, d9, d10, d11, d12, d13, d14, d15, d16, d17, d18, d19, d20, d21, d22, d23, d24, d25, d26, d27, d28, d29;
    wire [23:0] acc = 44*d0 + 37*d1 + 25*d2 + 24*d3 + 58*d4 + 4*d5 + 24*d6 + 58*d7 + 23*d8 + 46*d9 + 25*d10 + 35*d11 + 40*d12 + 8*d13 + 33*d14 + 12*d15 + 18*d16 + 9*d17 + 63*d18 + 4*d19 + 1*d20 + 45*d21 + 21*d22 + 43*d23 + 25*d24 + 33*d25 + 4*d26 + 57*d27 + 44*d28 + 11*d29;
    always @(posedge clk) begin
        if (!rst_n) begin
            d0 <= $unsigned(8'b0); d1 <= $unsigned(8'b0); d2 <= $unsigned(8'b0); d3 <= $unsigned(8'b0); d4 <= $unsigned(8'b0); d5 <= $unsigned(8'b0); d6 <= $unsigned(8'b0); d7 <= $unsigned(8'b0); d8 <= $unsigned(8'b0); d9 <= $unsigned(8'b0); d10 <= $unsigned(8'b0); d11 <= $unsigned(8'b0); d12 <= $unsigned(8'b0); d13 <= $unsigned(8'b0); d14 <= $unsigned(8'b0); d15 <= $unsigned(8'b0); d16 <= $unsigned(8'b0); d17 <= $unsigned(8'b0); d18 <= $unsigned(8'b0); d19 <= $unsigned(8'b0); d20 <= $unsigned(8'b0); d21 <= $unsigned(8'b0); d22 <= $unsigned(8'b0); d23 <= $unsigned(8'b0); d24 <= $unsigned(8'b0); d25 <= $unsigned(8'b0); d26 <= $unsigned(8'b0); d27 <= $unsigned(8'b0); d28 <= $unsigned(8'b0); d29 <= $unsigned(8'b0); y <= $unsigned(16'b0);
        end else begin
            d0 <= x;
            d1 <= d0;
            d2 <= d1;
            d3 <= d2;
            d4 <= d3;
            d5 <= d4;
            d6 <= d5;
            d7 <= d6;
            d8 <= d7;
            d9 <= d8;
            d10 <= d9;
            d11 <= d10;
            d12 <= d11;
            d13 <= d12;
            d14 <= d13;
            d15 <= d14;
            d16 <= d15;
            d17 <= d16;
            d18 <= d17;
            d19 <= d18;
            d20 <= d19;
            d21 <= d20;
            d22 <= d21;
            d23 <= d22;
            d24 <= d23;
            d25 <= d24;
            d26 <= d25;
            d27 <= d26;
            d28 <= d27;
            d29 <= d28;
            y <= acc[15:0];
        end
    end
endmodule
