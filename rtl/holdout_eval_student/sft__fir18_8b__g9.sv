module sft__fir18_8b__g9 (
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
    reg [23:0] acc10;
    reg [23:0] acc11;
    reg [23:0] acc12;
    reg [23:0] acc13;
    reg [23:0] acc14;
    reg [23:0] acc15;
    reg [23:0] acc16;
    reg [23:0] acc17;
    wire [7:0] xd1 = x;
    wire [7:0] xd2 = acc0[7:0];
    wire [7:0] xd3 = acc1[7:0];
    wire [7:0] xd4 = acc2[7:0];
    wire [7:0] xd5 = acc3[7:0];
    wire [7:0] xd6 = acc4[7:0];
    wire [7:0] xd7 = acc5[7:0];
    wire [7:0] xd8 = acc6[7:0];
    wire [7:0] xd9 = acc7[7:0];
    wire [7:0] xd10 = acc8[7:0];
    wire [7:0] xd11 = acc9[7:0];
    wire [7:0] xd12 = acc10[7:0];
    wire [7:0] xd13 = acc11[7:0];
    wire [7:0] xd14 = acc12[7:0];
    wire [7:0] xd15 = acc13[7:0];
    wire [7:0] xd16 = acc14[7:0];
    wire [7:0] xd17 = acc15[7:0];
    wire [7:0] xd18 = acc16[7:0];
    wire [7:0] xd19 = acc17[7:0];
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
            acc10 <= 24'd0;
            acc11 <= 24'd0;
            acc12 <= 24'd0;
            acc13 <= 24'd0;
            acc14 <= 24'd0;
            acc15 <= 24'd0;
            acc16 <= 24'd0;
            acc17 <= 24'd0;
            y <= 16'd0;
        end else begin
            acc0 <= 24'd3 * xd1 + acc1;
            acc1 <= 24'd5 * xd1 + acc2;
            acc2 <= 24'd7 * xd1 + acc3;
            acc3 <= 24'd9 * xd1 + acc4;
            acc4 <= 24'd11 * xd1 + acc5;
            acc5 <= 24'd13 * xd1 + acc6;
            acc6 <= 24'd15 * xd1 + acc7;
            acc7 <= 24'd17 * xd1 + acc8;
            acc8 <= 24'd19 * xd1 + acc9;
            acc9 <= 24'd19 * xd1 + acc10;
            acc10 <= 24'd17 * xd1 + acc11;
            acc11 <= 24'd15 * xd1 + acc12;
            acc12 <= 24'd13 * xd1 + acc13;
            acc13 <= 24'd11 * xd1 + acc14;
            acc14 <= 24'd9 * xd1 + acc15;
            acc15 <= 24'd7 * xd1 + acc16;
            acc16 <= 24'd5 * xd1 + acc17;
            acc17 <= 24'd3 * xd1;
            y <= acc0[15:0];
        end
    end
endmodule