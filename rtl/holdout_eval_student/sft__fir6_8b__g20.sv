module sft__fir6_8b__g20 (
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
    always @(posedge clk) begin
        if (!rst_n) begin
            acc0 <= 24'b0;
            acc1 <= 24'b0;
            acc2 <= 24'b0;
            acc3 <= 24'b0;
            acc4 <= 24'b0;
            acc5 <= 24'b0;
            y <= 16'b0;
        end else begin
            acc0 <= 8'd3 * x + acc1;
            acc1 <= 8'd5 * x + acc2;
            acc2 <= 8'd7 * x + acc3;
            acc3 <= 8'd7 * x + acc4;
            acc4 <= 8'd5 * x + acc5;
            acc5 <= 8'd3 * x;
            y <= acc0[15:0];
        end
    end
endmodule