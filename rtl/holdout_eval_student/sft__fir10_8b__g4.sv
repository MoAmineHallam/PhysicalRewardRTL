module sft__fir10_8b__g4 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [23:0] acc1; // 10-element delay line
    reg [23:0] acc2;
    reg [23:0] acc3;
    reg [23:0] acc4;
    reg [23:0] acc5;
    reg [23:0] acc6;
    reg [23:0] acc7;
    reg [23:0] acc8;
    reg [23:0] acc9;
    reg [23:0] acc10;
    wire [23:0] prod1 = 3 * x;
    wire [23:0] prod2 = 5 * x + acc1;
    wire [23:0] prod3 = 7 * x + acc2;
    wire [23:0] prod4 = 9 * x + acc3;
    wire [23:0] prod5 = 11 * x + acc4;
    wire [23:0] prod6 = 11 * x + acc5;
    wire [23:0] prod7 = 9 * x + acc6;
    wire [23:0] prod8 = 7 * x + acc7;
    wire [23:0] prod9 = 5 * x + acc8;
    wire [23:0] prod10 = 3 * x + acc9;
    always @(posedge clk) begin
        if (!rst_n) begin
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
            y <= 16'd0;
        end else begin
            acc1 <= prod1;
            acc2 <= prod2;
            acc3 <= prod3;
            acc4 <= prod4;
            acc5 <= prod5;
            acc6 <= prod6;
            acc7 <= prod7;
            acc8 <= prod8;
            acc9 <= prod9;
            acc10 <= prod10;
            y <= acc10[15:0];
        end
    end
endmodule