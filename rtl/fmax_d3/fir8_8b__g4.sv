module fir8_8b__g4 (
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
            y <= 16'd0;
        end else begin
            acc0 <= 8'd3 * x + acc1;
            acc1 <= 8'd5 * x + acc2;
            acc2 <= 8'd7 * x + acc3;
            acc3 <= 8'd9 * x + acc4;
            acc4 <= 8'd9 * x + acc5;
            acc5 <= 8'd7 * x + acc6;
            acc6 <= 8'd5 * x + acc7;
            acc7 <= 8'd3 * x;
            y <= acc0[15:0];
        end
    end
endmodule