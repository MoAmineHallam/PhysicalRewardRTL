module sft__poly6_v13_8b__g4 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [15:0] a0;
    reg [15:0] a1;
    reg [15:0] a2;
    reg [15:0] a3;
    reg [15:0] a4;
    reg [15:0] a5;
    reg [15:0] a6;
    reg [15:0] xd1;
    reg [15:0] xd2;
    reg [15:0] xd3;
    reg [15:0] xd4;
    reg [15:0] xd5;
    reg [15:0] xd6;
    always @(posedge clk) begin
        if (!rst_n) begin a0<=16'd0; a1<=16'd0; a2<=16'd0; a3<=16'd0; a4<=16'd0; a5<=16'd0; a6<=16'd0; xd1<=16'd0; xd2<=16'd0; xd3<=16'd0; xd4<=16'd0; xd5<=16'd0; xd6<=16'd0; y<=16'd0; end
        else begin
            a0 <= 16'd86;
            xd1 <= x;
            a1 <= a0 * xd1 + 16'd73;
            xd2 <= xd1;
            a2 <= a1 * xd2 + 16'd23;
            xd3 <= xd2;
            a3 <= a2 * xd3 + 16'd69;
            xd4 <= xd3;
            a4 <= a3 * xd4 + 16'd48;
            xd5 <= xd4;
            a5 <= a4 * xd5 + 16'd52;
            xd6 <= xd5;
            a6 <= a5 * xd6 + 16'd39;
            y <= a6;
        end
    end
endmodule
