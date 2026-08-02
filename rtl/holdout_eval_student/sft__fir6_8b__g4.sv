module sft__fir6_8b__g4 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [23:0] a0;
    reg [23:0] a1;
    reg [23:0] a2;
    reg [23:0] a3;
    reg [23:0] a4;
    reg [23:0] a5;
    always @(posedge clk) begin
        if (!rst_n) begin
            a0 <= 24'd0;
            a1 <= 24'd0;
            a2 <= 24'd0;
            a3 <= 24'd0;
            a4 <= 24'd0;
            a5 <= 24'd0;
            y <= 16'd0;
        end else begin
            a0 <= 24'd3 * x + a1;
            a1 <= 24'd5 * x + a2;
            a2 <= 24'd7 * x + a3;
            a3 <= 24'd7 * x + a4;
            a4 <= 24'd5 * x + a5;
            a5 <= 24'd3 * x;
            y <= a0[15:0];
        end
    end
endmodule