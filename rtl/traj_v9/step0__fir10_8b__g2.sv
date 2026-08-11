module step0__fir10_8b__g2 (
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
    wire [15:0] y_reg = 8'd3 * xd0 + 8'd5 * xd1 + 8'd7 * xd2 + 8'd9 * xd3 + 8'd11 * xd4 + 8'd11 * xd5 + 8'd9 * xd6 + 8'd7 * xd7 + 8'd5 * xd8 + 8'd3 * xd9;
    always @(posedge clk) begin
        if (!rst_n) begin
            y <= 16'd0;
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
        end else begin
            y <= y_reg;
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
        end
    end
endmodule