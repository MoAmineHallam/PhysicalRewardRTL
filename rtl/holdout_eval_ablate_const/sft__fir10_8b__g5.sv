module sft__fir10_8b__g5 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  xd0, xd1, xd2, xd3, xd4, xd5, xd6, xd7, xd8, xd9;
    reg  [15:0] p0, p1, p2, p3, p4, p5, p6, p7, p8, p9;
    always @(posedge clk) begin
        if (!rst_n) begin
            xd0 <= 8'd0; xd1 <= 8'd0; xd2 <= 8'd0; xd3 <= 8'd0; xd4 <= 8'd0; xd5 <= 8'd0; xd6 <= 8'd0; xd7 <= 8'd0; xd8 <= 8'd0; xd9 <= 8'd0;
            p0 <= 16'd0; p1 <= 16'd0; p2 <= 16'd0; p3 <= 16'd0; p4 <= 16'd0; p5 <= 16'd0; p6 <= 16'd0; p7 <= 16'd0; p8 <= 16'd0; p9 <= 16'd0; y <= 16'd0;
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
            p0 <= 8'd3 * xd0;
            p1 <= 8'd5 * xd1;
            p2 <= 8'd7 * xd2;
            p3 <= 8'd9 * xd3;
            p4 <= 8'd11 * xd4;
            p5 <= 8'd11 * xd5;
            p6 <= 8'd9 * xd6;
            p7 <= 8'd7 * xd7;
            p8 <= 8'd5 * xd8;
            p9 <= 8'd3 * xd9;
            y <= p0 + p1 + p2 + p3 + p4 + p5 + p6 + p7 + p8 + p9;
        end
    end
endmodule