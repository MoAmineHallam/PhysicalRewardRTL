module sft__fir6_8b__g5 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [7:0] xd0;
    reg [7:0] xd1;
    reg [7:0] xd2;
    reg [7:0] xd3;
    reg [7:0] xd4;
    reg [7:0] xd5;
    reg [15:0] p0, p1, p2, p3, p4, p5;
    always @(*) begin
        p0 = 8'd3 * x;
        p1 = 8'd5 * xd0;
        p2 = 8'd7 * xd1;
        p3 = 8'd7 * xd2;
        p4 = 8'd5 * xd3;
        p5 = 8'd3 * xd4;
    end
    always @(posedge clk) begin
        if (!rst_n) begin
            y <= 16'd0;
            xd0 <= 8'd0;
            xd1 <= 8'd0;
            xd2 <= 8'd0;
            xd3 <= 8'd0;
            xd4 <= 8'd0;
            xd5 <= 8'd0;
        end else begin
            y <= p0 + p1 + p2 + p3 + p4 + p5;
            xd5 <= xd4;
            xd4 <= xd3;
            xd3 <= xd2;
            xd2 <= xd1;
            xd1 <= xd0;
            xd0 <= x;
        end
    end
endmodule