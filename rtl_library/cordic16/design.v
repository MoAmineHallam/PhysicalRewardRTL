// 16-iteration rotation-mode CORDIC, unrolled COMBINATIONAL shift-add chain
// (the long path -> lower Fmax; pipeline the iterations to go faster).
module cordic16 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    wire signed [23:0] x0w = 24'sd9949;
    wire signed [23:0] y0w = 24'sd0;
    wire signed [23:0] z0w = $signed({16'b0, x});
    wire ge0 = (z0w >= 0);
    wire signed [23:0] x1 = ge0 ? (x0w - (y0w >>> 0)) : (x0w + (y0w >>> 0));
    wire signed [23:0] y1 = ge0 ? (y0w + (x0w >>> 0)) : (y0w - (x0w >>> 0));
    wire signed [23:0] z1 = ge0 ? (z0w - 24'sd128) : (z0w + 24'sd128);
    wire ge1 = (z1 >= 0);
    wire signed [23:0] x2 = ge1 ? (x1 - (y1 >>> 1)) : (x1 + (y1 >>> 1));
    wire signed [23:0] y2 = ge1 ? (y1 + (x1 >>> 1)) : (y1 - (x1 >>> 1));
    wire signed [23:0] z2 = ge1 ? (z1 - 24'sd76) : (z1 + 24'sd76);
    wire ge2 = (z2 >= 0);
    wire signed [23:0] x3 = ge2 ? (x2 - (y2 >>> 2)) : (x2 + (y2 >>> 2));
    wire signed [23:0] y3 = ge2 ? (y2 + (x2 >>> 2)) : (y2 - (x2 >>> 2));
    wire signed [23:0] z3 = ge2 ? (z2 - 24'sd40) : (z2 + 24'sd40);
    wire ge3 = (z3 >= 0);
    wire signed [23:0] x4 = ge3 ? (x3 - (y3 >>> 3)) : (x3 + (y3 >>> 3));
    wire signed [23:0] y4 = ge3 ? (y3 + (x3 >>> 3)) : (y3 - (x3 >>> 3));
    wire signed [23:0] z4 = ge3 ? (z3 - 24'sd20) : (z3 + 24'sd20);
    wire ge4 = (z4 >= 0);
    wire signed [23:0] x5 = ge4 ? (x4 - (y4 >>> 4)) : (x4 + (y4 >>> 4));
    wire signed [23:0] y5 = ge4 ? (y4 + (x4 >>> 4)) : (y4 - (x4 >>> 4));
    wire signed [23:0] z5 = ge4 ? (z4 - 24'sd10) : (z4 + 24'sd10);
    wire ge5 = (z5 >= 0);
    wire signed [23:0] x6 = ge5 ? (x5 - (y5 >>> 5)) : (x5 + (y5 >>> 5));
    wire signed [23:0] y6 = ge5 ? (y5 + (x5 >>> 5)) : (y5 - (x5 >>> 5));
    wire signed [23:0] z6 = ge5 ? (z5 - 24'sd5) : (z5 + 24'sd5);
    wire ge6 = (z6 >= 0);
    wire signed [23:0] x7 = ge6 ? (x6 - (y6 >>> 6)) : (x6 + (y6 >>> 6));
    wire signed [23:0] y7 = ge6 ? (y6 + (x6 >>> 6)) : (y6 - (x6 >>> 6));
    wire signed [23:0] z7 = ge6 ? (z6 - 24'sd3) : (z6 + 24'sd3);
    wire ge7 = (z7 >= 0);
    wire signed [23:0] x8 = ge7 ? (x7 - (y7 >>> 7)) : (x7 + (y7 >>> 7));
    wire signed [23:0] y8 = ge7 ? (y7 + (x7 >>> 7)) : (y7 - (x7 >>> 7));
    wire signed [23:0] z8 = ge7 ? (z7 - 24'sd1) : (z7 + 24'sd1);
    wire ge8 = (z8 >= 0);
    wire signed [23:0] x9 = ge8 ? (x8 - (y8 >>> 8)) : (x8 + (y8 >>> 8));
    wire signed [23:0] y9 = ge8 ? (y8 + (x8 >>> 8)) : (y8 - (x8 >>> 8));
    wire signed [23:0] z9 = ge8 ? (z8 - 24'sd1) : (z8 + 24'sd1);
    wire ge9 = (z9 >= 0);
    wire signed [23:0] x10 = ge9 ? (x9 - (y9 >>> 9)) : (x9 + (y9 >>> 9));
    wire signed [23:0] y10 = ge9 ? (y9 + (x9 >>> 9)) : (y9 - (x9 >>> 9));
    wire signed [23:0] z10 = ge9 ? (z9 - 24'sd0) : (z9 + 24'sd0);
    wire ge10 = (z10 >= 0);
    wire signed [23:0] x11 = ge10 ? (x10 - (y10 >>> 10)) : (x10 + (y10 >>> 10));
    wire signed [23:0] y11 = ge10 ? (y10 + (x10 >>> 10)) : (y10 - (x10 >>> 10));
    wire signed [23:0] z11 = ge10 ? (z10 - 24'sd0) : (z10 + 24'sd0);
    wire ge11 = (z11 >= 0);
    wire signed [23:0] x12 = ge11 ? (x11 - (y11 >>> 11)) : (x11 + (y11 >>> 11));
    wire signed [23:0] y12 = ge11 ? (y11 + (x11 >>> 11)) : (y11 - (x11 >>> 11));
    wire signed [23:0] z12 = ge11 ? (z11 - 24'sd0) : (z11 + 24'sd0);
    wire ge12 = (z12 >= 0);
    wire signed [23:0] x13 = ge12 ? (x12 - (y12 >>> 12)) : (x12 + (y12 >>> 12));
    wire signed [23:0] y13 = ge12 ? (y12 + (x12 >>> 12)) : (y12 - (x12 >>> 12));
    wire signed [23:0] z13 = ge12 ? (z12 - 24'sd0) : (z12 + 24'sd0);
    wire ge13 = (z13 >= 0);
    wire signed [23:0] x14 = ge13 ? (x13 - (y13 >>> 13)) : (x13 + (y13 >>> 13));
    wire signed [23:0] y14 = ge13 ? (y13 + (x13 >>> 13)) : (y13 - (x13 >>> 13));
    wire signed [23:0] z14 = ge13 ? (z13 - 24'sd0) : (z13 + 24'sd0);
    wire ge14 = (z14 >= 0);
    wire signed [23:0] x15 = ge14 ? (x14 - (y14 >>> 14)) : (x14 + (y14 >>> 14));
    wire signed [23:0] y15 = ge14 ? (y14 + (x14 >>> 14)) : (y14 - (x14 >>> 14));
    wire signed [23:0] z15 = ge14 ? (z14 - 24'sd0) : (z14 + 24'sd0);
    wire ge15 = (z15 >= 0);
    wire signed [23:0] x16 = ge15 ? (x15 - (y15 >>> 15)) : (x15 + (y15 >>> 15));
    wire signed [23:0] y16 = ge15 ? (y15 + (x15 >>> 15)) : (y15 - (x15 >>> 15));
    wire signed [23:0] z16 = ge15 ? (z15 - 24'sd0) : (z15 + 24'sd0);
    always @(posedge clk) begin
        if (!rst_n) y <= 16'd0;
        else        y <= x16[15:0];
    end
endmodule
