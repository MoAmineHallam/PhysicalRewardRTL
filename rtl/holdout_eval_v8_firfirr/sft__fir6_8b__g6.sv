module sft__fir6_8b__g6 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  xd1;
    reg  [7:0]  xd2;
    reg  [7:0]  xd3;
    reg  [7:0]  xd4;
    reg  [7:0]  xd5;
    reg  [15:0] p1, p2, p3, p4, p5, p6;
    always @(posedge clk) begin
        if (!rst_n) begin
            xd1 <= 8'd0; xd2 <= 8'd0; xd3 <= 8'd0; xd4 <= 8'd0; xd5 <= 8'd0;
            p1 <= 16'd0; p2 <= 16'd0; p3 <= 16'd0; p4 <= 16'd0; p5 <= 16'd0; p6 <= 16'd0; y <= 16'd0;
        end else begin
            xd1 <= x;
            xd2 <= xd1;
            xd3 <= xd2;
            xd4 <= xd3;
            xd5 <= xd4;
            p1 <= 8'd3 * x;
            p2 <= 8'd5 * xd1;
            p3 <= 8'd7 * xd2;
            p4 <= 8'd7 * xd3;
            p5 <= 8'd5 * xd4;
            p6 <= 8'd3 * xd5;
            y <= p1 + p2 + p3 + p4 + p5 + p6;
        end
    end
endmodule