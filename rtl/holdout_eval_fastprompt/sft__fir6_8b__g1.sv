module sft__fir6_8b__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [23:0] a0, a1, a2, a3, a4, a5;
    wire [23:0] prod0 = x * 8'd3;
    wire [23:0] prod1 = x * 8'd5;
    wire [23:0] prod2 = x * 8'd7;
    wire [23:0] prod3 = x * 8'd7;
    wire [23:0] prod4 = x * 8'd5;
    wire [23:0] prod5 = x * 8'd3;
    always @(posedge clk) begin
        if (!rst_n) begin
            a0 <= 24'd0; a1 <= 24'd0; a2 <= 24'd0; a3 <= 24'd0; a4 <= 24'd0; a5 <= 24'd0; y <= 16'd0;
        end else begin
            a0 <= prod0;
            a1 <= prod1 + a0;
            a2 <= prod2 + a1;
            a3 <= prod3 + a2;
            a4 <= prod4 + a3;
            a5 <= prod5 + a4;
            y <= a5 & 16'hFFFF;
        end
    end
endmodule