module firr16__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  xd0;
    reg  [7:0]  xd1;
    reg  [7:0]  xd2;
    reg  [7:0]  xd3;
    reg  [7:0]  xd4;
    reg  [7:0]  xd5;
    reg  [7:0]  xd6;
    reg  [7:0]  xd7;
    reg  [7:0]  xd8;
    reg  [7:0]  xd9;
    reg  [7:0]  xd10;
    reg  [7:0]  xd11;
    reg  [7:0]  xd12;
    reg  [7:0]  xd13;
    reg  [7:0]  xd14;
    reg  [7:0]  xd15;
    always @(posedge clk) begin
        if (!rst_n) begin
            xd0 <= 8'd0;
            xd1 <= 8'd0;
            xd2 <= 8'd0;
            xd3 <= 8'd0;
            xd4 <= 8'd0;
            xd5 <= 8'd0;
            xd6 <= 8'd0;
            xd7 <= 8'd0;
            xd8 <= 8'd0;
            xd9 <= 8'd0;
            xd10 <= 8'd0;
            xd11 <= 8'd0;
            xd12 <= 8'd0;
            xd13 <= 8'd0;
            xd14 <= 8'd0;
            xd15 <= 8'd0;
            y <= 16'd0;
        end else begin
            xd0 <= x;
            xd1 <= xd0;
            xd2 <= xd1;
            xd3 <= xd2;
            xd4 <= xd3;
            xd5 <= xd4;
            xd6 <= xd5;
            xd7 <= xd6;
            xd8 <= xd7;
            xd9 <= xd8;
            xd10 <= xd9;
            xd11 <= xd10;
            xd12 <= xd11;
            xd13 <= xd12;
            xd14 <= xd13;
            xd15 <= xd14;
            y <= (1 * xd0) + (2 * xd1) + (3 * xd2) + (4 * xd3) + (5 * xd4) + (6 * xd5) + (7 * xd6) + (8 * xd7) + (9 * xd8) + (10 * xd9) + (11 * xd10) + (12 * xd11) + (13 * xd12) + (14 * xd13) + (15 * xd14) + (16 * xd15);
        end
    end
endmodule