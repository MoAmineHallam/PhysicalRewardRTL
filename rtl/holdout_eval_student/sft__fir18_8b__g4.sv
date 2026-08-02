module sft__fir18_8b__g4 (
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
    always @(posedge clk) begin
        if (!rst_n) begin
            acc0 <= 24'b0;
            acc1 <= 24'b0;
            acc2 <= 24'b0;
            acc3 <= 24'b0;
            acc4 <= 24'b0;
            acc5 <= 24'b0;
            acc6 <= 24'b0;
            acc7 <= 24'b0;
            acc8 <= 24'b0;
            acc9 <= 24'b0;
            acc10 <= 24'b0;
            acc11 <= 24'b0;
            acc12 <= 24'b0;
            acc13 <= 24'b0;
            acc14 <= 24'b0;
            acc15 <= 24'b0;
            acc16 <= 24'b0;
            acc17 <= 24'b0;
            y <= 16'b0;
        end else begin
            acc0 <= 8'd3 * x + acc1;
            acc1 <= 8'd5 * x + acc2;
            acc2 <= 8'd7 * x + acc3;
            acc3 <= 8'd9 * x + acc4;
            acc4 <= 8'd11 * x + acc5;
            acc5 <= 8'd13 * x + acc6;
            acc6 <= 8'd15 * x + acc7;
            acc7 <= 8'd17 * x + acc8;
            acc8 <= 8'd19 * x + acc9;
            acc9 <= 8'd19 * x + acc10;
            acc10 <= 8'd17 * x + acc11;
            acc11 <= 8'd15 * x + acc12;
            acc12 <= 8'd13 * x + acc13;
            acc13 <= 8'd11 * x + acc14;
            acc14 <= 8'd9 * x + acc15;
            acc15 <= 8'd7 * x + acc16;
            acc16 <= 8'd5 * x + acc17;
            acc17 <= 8'd3 * x;
            y <= acc0[15:0];
        end
    end
endmodule