module sft__fir10_8b__g9 (
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
            acc0 <= 24'd3 * xd1 + acc1;
            acc1 <= 24'd5 * xd1 + acc2;
            acc2 <= 24'd7 * xd1 + acc3;
            acc3 <= 24'd9 * xd1 + acc4;
            acc4 <= 24'd11 * xd1 + acc5;
            acc5 <= 24'd11 * xd1 + acc6;
            acc6 <= 24'd9 * xd1 + acc7;
            acc7 <= 24'd7 * xd1 + acc8;
            acc8 <= 24'd5 * xd1 + acc9;
            acc9 <= 24'd3 * xd1;
            xd1 <= x;
            xd2 <= xd1;
            xd3 <= xd2;
            xd4 <= xd3;
            xd5 <= xd4;
            xd6 <= xd5;
            xd7 <= xd6;
            xd8 <= xd7;
            xd9 <= xd8;
            y <= acc0[15:0];
        end
    end
endmodule