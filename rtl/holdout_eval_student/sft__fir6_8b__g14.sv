module sft__fir6_8b__g14 (
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
    wire [7:0] xd1 = x;
    wire [7:0] xd2 = acc0[8:0];
    wire [7:0] xd3 = acc1[8:0];
    wire [7:0] xd4 = acc2[8:0];
    wire [7:0] xd5 = acc3[8:0];
    wire [7:0] xd6 = acc4[8:0];
    wire [7:0] xd7 = acc5[8:0];
    always @(posedge clk) begin
        if (!rst_n) begin
            acc0 <= 24'd0;
            acc1 <= 24'd0;
            acc2 <= 24'd0;
            acc3 <= 24'd0;
            acc4 <= 24'd0;
            acc5 <= 24'd0;
            y <= 16'd0;
        end else begin
            acc0 <= 24'd3 * xd1 + acc1;
            acc1 <= 24'd5 * xd1 + acc2;
            acc2 <= 24'd7 * xd1 + acc3;
            acc3 <= 24'd7 * xd1 + acc4;
            acc4 <= 24'd5 * xd1 + acc5;
            acc5 <= 24'd3 * xd1;
            y <= acc0[15:0];
        end
    end
endmodule