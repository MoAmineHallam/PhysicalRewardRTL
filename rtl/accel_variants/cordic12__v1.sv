// 12-iteration rotation-mode CORDIC, FULLY PIPELINED (one register per
// iteration) -> short per-stage path, higher Fmax. Same result, +12 latency.
module cordic12__v1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    wire signed [23:0] x0w = 24'sd9949;
    wire signed [23:0] y0w = 24'sd0;
    wire signed [23:0] z0w = $signed({16'b0, x});
    reg signed [23:0] xr1, yr1, zr1;
    reg signed [23:0] xr2, yr2, zr2;
    reg signed [23:0] xr3, yr3, zr3;
    reg signed [23:0] xr4, yr4, zr4;
    reg signed [23:0] xr5, yr5, zr5;
    reg signed [23:0] xr6, yr6, zr6;
    reg signed [23:0] xr7, yr7, zr7;
    reg signed [23:0] xr8, yr8, zr8;
    reg signed [23:0] xr9, yr9, zr9;
    reg signed [23:0] xr10, yr10, zr10;
    reg signed [23:0] xr11, yr11, zr11;
    reg signed [23:0] xr12, yr12, zr12;
    integer k;
    always @(posedge clk) begin
        if (!rst_n) begin xr1<=0; yr1<=0; zr1<=0; xr2<=0; yr2<=0; zr2<=0; xr3<=0; yr3<=0; zr3<=0; xr4<=0; yr4<=0; zr4<=0; xr5<=0; yr5<=0; zr5<=0; xr6<=0; yr6<=0; zr6<=0; xr7<=0; yr7<=0; zr7<=0; xr8<=0; yr8<=0; zr8<=0; xr9<=0; yr9<=0; zr9<=0; xr10<=0; yr10<=0; zr10<=0; xr11<=0; yr11<=0; zr11<=0; xr12<=0; yr12<=0; zr12<=0; y <= 16'd0; end
        else begin
            xr1 <= (z0w >= 0) ? (x0w - (y0w >>> 0)) : (x0w + (y0w >>> 0));
            yr1 <= (z0w >= 0) ? (y0w + (x0w >>> 0)) : (y0w - (x0w >>> 0));
            zr1 <= (z0w >= 0) ? (z0w - 24'sd128) : (z0w + 24'sd128);
            xr2 <= (zr1 >= 0) ? (xr1 - (yr1 >>> 1)) : (xr1 + (yr1 >>> 1));
            yr2 <= (zr1 >= 0) ? (yr1 + (xr1 >>> 1)) : (yr1 - (xr1 >>> 1));
            zr2 <= (zr1 >= 0) ? (zr1 - 24'sd76) : (zr1 + 24'sd76);
            xr3 <= (zr2 >= 0) ? (xr2 - (yr2 >>> 2)) : (xr2 + (yr2 >>> 2));
            yr3 <= (zr2 >= 0) ? (yr2 + (xr2 >>> 2)) : (yr2 - (xr2 >>> 2));
            zr3 <= (zr2 >= 0) ? (zr2 - 24'sd40) : (zr2 + 24'sd40);
            xr4 <= (zr3 >= 0) ? (xr3 - (yr3 >>> 3)) : (xr3 + (yr3 >>> 3));
            yr4 <= (zr3 >= 0) ? (yr3 + (xr3 >>> 3)) : (yr3 - (xr3 >>> 3));
            zr4 <= (zr3 >= 0) ? (zr3 - 24'sd20) : (zr3 + 24'sd20);
            xr5 <= (zr4 >= 0) ? (xr4 - (yr4 >>> 4)) : (xr4 + (yr4 >>> 4));
            yr5 <= (zr4 >= 0) ? (yr4 + (xr4 >>> 4)) : (yr4 - (xr4 >>> 4));
            zr5 <= (zr4 >= 0) ? (zr4 - 24'sd10) : (zr4 + 24'sd10);
            xr6 <= (zr5 >= 0) ? (xr5 - (yr5 >>> 5)) : (xr5 + (yr5 >>> 5));
            yr6 <= (zr5 >= 0) ? (yr5 + (xr5 >>> 5)) : (yr5 - (xr5 >>> 5));
            zr6 <= (zr5 >= 0) ? (zr5 - 24'sd5) : (zr5 + 24'sd5);
            xr7 <= (zr6 >= 0) ? (xr6 - (yr6 >>> 6)) : (xr6 + (yr6 >>> 6));
            yr7 <= (zr6 >= 0) ? (yr6 + (xr6 >>> 6)) : (yr6 - (xr6 >>> 6));
            zr7 <= (zr6 >= 0) ? (zr6 - 24'sd3) : (zr6 + 24'sd3);
            xr8 <= (zr7 >= 0) ? (xr7 - (yr7 >>> 7)) : (xr7 + (yr7 >>> 7));
            yr8 <= (zr7 >= 0) ? (yr7 + (xr7 >>> 7)) : (yr7 - (xr7 >>> 7));
            zr8 <= (zr7 >= 0) ? (zr7 - 24'sd1) : (zr7 + 24'sd1);
            xr9 <= (zr8 >= 0) ? (xr8 - (yr8 >>> 8)) : (xr8 + (yr8 >>> 8));
            yr9 <= (zr8 >= 0) ? (yr8 + (xr8 >>> 8)) : (yr8 - (xr8 >>> 8));
            zr9 <= (zr8 >= 0) ? (zr8 - 24'sd1) : (zr8 + 24'sd1);
            xr10 <= (zr9 >= 0) ? (xr9 - (yr9 >>> 9)) : (xr9 + (yr9 >>> 9));
            yr10 <= (zr9 >= 0) ? (yr9 + (xr9 >>> 9)) : (yr9 - (xr9 >>> 9));
            zr10 <= (zr9 >= 0) ? (zr9 - 24'sd0) : (zr9 + 24'sd0);
            xr11 <= (zr10 >= 0) ? (xr10 - (yr10 >>> 10)) : (xr10 + (yr10 >>> 10));
            yr11 <= (zr10 >= 0) ? (yr10 + (xr10 >>> 10)) : (yr10 - (xr10 >>> 10));
            zr11 <= (zr10 >= 0) ? (zr10 - 24'sd0) : (zr10 + 24'sd0);
            xr12 <= (zr11 >= 0) ? (xr11 - (yr11 >>> 11)) : (xr11 + (yr11 >>> 11));
            yr12 <= (zr11 >= 0) ? (yr11 + (xr11 >>> 11)) : (yr11 - (xr11 >>> 11));
            zr12 <= (zr11 >= 0) ? (zr11 - 24'sd0) : (zr11 + 24'sd0);
            y <= xr12[15:0];
        end
    end
endmodule
