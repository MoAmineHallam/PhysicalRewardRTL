module sft__fir6_8b__g11 (
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
    wire [15:0] y_reg = 8'd3 * x +
                        8'd5 * xd0 +
                        8'd7 * xd1 +
                        8'd7 * xd2 +
                        8'd5 * xd3 +
                        8'd3 * xd4;
    always @(posedge clk) begin
        if (!rst_n) begin
            xd0 <= 8'd0; xd1 <= 8'd0; xd2 <= 8'd0; xd3 <= 8'd0; xd4 <= 8'd0; xd5 <= 8'd0; y <= 16'd0;
        end else begin
            xd0 <= x;
            xd1 <= xd0;
            xd2 <= xd1;
            xd3 <= xd2;
            xd4 <= xd3;
            xd5 <= xd4;
            y <= y_reg;
        end
    end
endmodule