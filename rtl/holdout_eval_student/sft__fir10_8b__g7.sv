module sft__fir10_8b__g7 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [23:0] acc0;
    reg [23:0] acc1;
    reg [23:0] acc2;
    reg [23:0] acc3;
    reg [23:0] acc4;
    reg [23:0] acc5;
    reg [23:0] acc6;
    reg [23:0] acc7;
    reg [23:0] acc8;
    reg [23:0] acc9;
    reg [7:0] xd0;
    reg [7:0] xd1;
    reg [7:0] xd2;
    reg [7:0] xd3;
    reg [7:0] xd4;
    reg [7:0] xd5;
    reg [7:0] xd6;
    reg [7:0] xd7;
    reg [7:0] xd8;
    reg [7:0] xd9;
    always @(posedge clk) begin
        if (!rst_n) begin
            acc0 <= 24'd0;
            acc1 <= 24'd0;
            acc2 <= 24'd0;
            acc3 <= 24'd0;
            acc4 <= 24'd0;
            acc5 <= 24'd0;
            acc6 <= 24'd0;
            acc7 <= 24'd0;
            acc8 <= 24'd0;
            acc9 <= 24'd0;
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
            y <= 16'd0;
        end else begin
            acc0 <= 8'd3 * xd0 + acc1;
            acc1 <= 8'd5 * xd0 + acc2;
            acc2 <= 8'd7 * xd0 + acc3;
            acc3 <= 8'd9 * xd0 + acc4;
            acc4 <= 8'd11 * xd0 + acc5;
            acc5 <= 8'd11 * xd0 + acc6;
            acc6 <= 8'd9 * xd0 + acc7;
            acc7 <= 8'd7 * xd0 + acc8;
            acc8 <= 8'd5 * xd0 + acc9;
            acc9 <= 8'd3 * xd0;
            xd0 <= xd1;
            xd1 <= xd2;
            xd2 <= xd3;
            xd3 <= xd4;
            xd4 <= xd5;
            xd5 <= xd6;
            xd6 <= xd7;
            xd7 <= xd8;
            xd8 <= xd9;
            xd9 <= x;
            y <= acc0[15:0];
        end
    end
endmodule