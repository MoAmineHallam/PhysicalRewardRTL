module sft__fir10_8b__g1 (
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
    reg [23:0] a6;
    reg [23:0] a7;
    reg [23:0] a8;
    reg [23:0] a9;
    reg [7:0] xd1;
    always @(posedge clk) begin
        if (!rst_n) begin
            y <= 16'd0;
            a0 <= 24'd0;
            a1 <= 24'd0;
            a2 <= 24'd0;
            a3 <= 24'd0;
            a4 <= 24'd0;
            a5 <= 24'd0;
            a6 <= 24'd0;
            a7 <= 24'd0;
            a8 <= 24'd0;
            a9 <= 24'd0;
            xd1 <= 8'd0;
        end else begin
            y <= {a9[15:0], a8[15:0], a7[15:0], a6[15:0], a5[15:0], a4[15:0], a3[15:0], a2[15:0], a1[15:0], a0[15:0]};
            a0 <= 8'd3 * xd1 + a1;
            a1 <= 8'd5 * xd1 + a2;
            a2 <= 8'd7 * xd1 + a3;
            a3 <= 8'd9 * xd1 + a4;
            a4 <= 8'd11 * xd1 + a5;
            a5 <= 8'd11 * xd1 + a6;
            a6 <= 8'd9 * xd1 + a7;
            a7 <= 8'd7 * xd1 + a8;
            a8 <= 8'd5 * xd1 + a9;
            a9 <= 8'd3 * xd1;
            xd1 <= x;
        end
    end
endmodule