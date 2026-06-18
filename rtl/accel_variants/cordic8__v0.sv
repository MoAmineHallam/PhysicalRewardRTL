// 8-iteration rotation-mode CORDIC, unrolled COMBINATIONAL shift-add chain
// (the long path -> lower Fmax; pipeline the iterations to go faster).
module cordic8__v0 (
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
    always @(posedge clk) begin
        if (!rst_n) y <= 16'd0;
        else        y <= x8[15:0];
    end
endmodule
