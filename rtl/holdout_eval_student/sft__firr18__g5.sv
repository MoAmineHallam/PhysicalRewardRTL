module sft__firr18__g5 (
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
    reg [23:0] a10;
    reg [23:0] a11;
    reg [23:0] a12;
    reg [23:0] a13;
    reg [23:0] a14;
    reg [23:0] a15;
    reg [23:0] a16;
    reg [23:0] a17;
    always @(posedge clk) begin
        if (!rst_n) begin
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
            a10 <= 24'd0;
            a11 <= 24'd0;
            a12 <= 24'd0;
            a13 <= 24'd0;
            a14 <= 24'd0;
            a15 <= 24'd0;
            a16 <= 24'd0;
            a17 <= 24'd0;
            y <= 16'd0;
        end else begin
            a0 <= 8'd1 * x + a1;
            a1 <= 8'd2 * x + a2;
            a2 <= 8'd3 * x + a3;
            a3 <= 8'd4 * x + a4;
            a4 <= 8'd5 * x + a5;
            a5 <= 8'd6 * x + a6;
            a6 <= 8'd7 * x + a7;
            a7 <= 8'd8 * x + a8;
            a8 <= 8'd9 * x + a9;
            a9 <= 8'd10 * x + a10;
            a10 <= 8'd11 * x + a11;
            a11 <= 8'd12 * x + a12;
            a12 <= 8'd13 * x + a13;
            a13 <= 8'd14 * x + a14;
            a14 <= 8'd15 * x + a15;
            a15 <= 8'd16 * x + a16;
            a16 <= 8'd17 * x + a17;
            a17 <= 8'd18 * x;
            y <= a0[15:0];
        end
    end
endmodule