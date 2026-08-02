module sft__fir6_8b__g17 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [23:0] acc1;
    reg [23:0] acc2;
    reg [23:0] acc3;
    reg [23:0] acc4;
    reg [23:0] acc5;
    reg [23:0] acc6;
    wire [7:0] xd0 = x;
    wire [7:0] xd1 = acc1[23:8];
    wire [7:0] xd2 = acc2[23:8];
    wire [7:0] xd3 = acc3[23:8];
    wire [7:0] xd4 = acc4[23:8];
    wire [7:0] xd5 = acc5[23:8];
    wire [7:0] xd6 = acc6[23:8];
    always @(posedge clk) begin
        if (!rst_n) begin
            acc1 <= 24'b0;
            acc2 <= 24'b0;
            acc3 <= 24'b0;
            acc4 <= 24'b0;
            acc5 <= 24'b0;
            acc6 <= 24'b0;
            y <= 16'b0;
        end else begin
            acc1 <= 8'd3 * xd0 + acc2;
            acc2 <= 8'd5 * xd0 + acc3;
            acc3 <= 8'd7 * xd0 + acc4;
            acc4 <= 8'd7 * xd0 + acc5;
            acc5 <= 8'd5 * xd0 + acc6;
            acc6 <= 8'd3 * xd0;
            y <= acc1[15:0];
        end
    end
endmodule