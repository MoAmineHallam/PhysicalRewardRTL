module sft__fir6_8b__g12 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  xs [0:5];
    reg  [15:0] y2;
    reg  [15:0] y3;
    reg  [15:0] y4;
    reg  [15:0] y5;
    reg  [15:0] y6;
    always @(posedge clk) begin
        if (!rst_n) begin
            for (int i = 0; i < 6; i = i + 1) xs[i] <= 8'd0;
            y <= 16'd0;
            y2 <= 16'd0;
            y3 <= 16'd0;
            y4 <= 16'd0;
            y5 <= 16'd0;
            y6 <= 16'd0;
        end else begin
            xs[0] <= x;
            for (int i = 1; i < 6; i = i + 1) xs[i] <= xs[i-1];
            y <= (8'd3 * xs[0]) + (8'd5 * xs[1]) + (8'd7 * xs[2]) + (8'd7 * xs[3]) + (8'd5 * xs[4]) + (8'd3 * xs[5]);
            y2 <= (8'd3 * xs[1]) + (8'd5 * xs[2]) + (8'd7 * xs[3]) + (8'd7 * xs[4]) + (8'd5 * xs[5]) + (8'd3 * xs[0]);
            y3 <= (8'd3 * xs[2]) + (8'd5 * xs[3]) + (8'd7 * xs[4]) + (8'd7 * xs[5]) + (8'd5 * xs[0]) + (8'd3 * xs[1]);
            y4 <= (8'd3 * xs[3]) + (8'd5 * xs[4]) + (8'd7 * xs[5]) + (8'd7 * xs[0]) + (8'd5 * xs[1]) + (8'd3 * xs[2]);
            y5 <= (8'd3 * xs[4]) + (8'd5 * xs[5]) + (8'd7 * xs[0]) + (8'd7 * xs[1]) + (8'd5 * xs[2]) + (8'd3 * xs[3]);
            y6 <= (8'd3 * xs[5]) + (8'd5 * xs[0]) + (8'd7 * xs[1]) + (8'd7 * xs[2]) + (8'd5 * xs[3]) + (8'd3 * xs[4]);
        end
    end
    always @(posedge clk) y <= y2;
    always @(posedge clk) y2 <= y3;
    always @(posedge clk) y3 <= y4;
    always @(posedge clk) y4 <= y5;
    always @(posedge clk) y5 <= y6;
    always @(posedge clk) y6 <= (8'd3 * xs[0]) + (8'd5 * xs[1]) + (8'd7 * xs[2]) + (8'd7 * xs[3]) + (8'd5 * xs[4]) + (8'd3 * xs[5]);
endmodule