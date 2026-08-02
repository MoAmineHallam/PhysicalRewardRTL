module sft__fir18_8b__g13 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [23:0] ac0;
    reg [23:0] ac1;
    reg [23:0] ac2;
    reg [23:0] ac3;
    reg [23:0] ac4;
    reg [23:0] ac5;
    reg [23:0] ac6;
    reg [23:0] ac7;
    reg [23:0] ac8;
    reg [23:0] ac9;
    reg [23:0] ac10;
    reg [23:0] ac11;
    reg [23:0] ac12;
    reg [23:0] ac13;
    reg [23:0] ac14;
    reg [23:0] ac15;
    reg [23:0] ac16;
    reg [23:0] ac17;
    always @(posedge clk) begin
        if (!rst_n) begin
            ac0 <= 24'd0;
            ac1 <= 24'd0;
            ac2 <= 24'd0;
            ac3 <= 24'd0;
            ac4 <= 24'd0;
            ac5 <= 24'd0;
            ac6 <= 24'd0;
            ac7 <= 24'd0;
            ac8 <= 24'd0;
            ac9 <= 24'd0;
            ac10 <= 24'd0;
            ac11 <= 24'd0;
            ac12 <= 24'd0;
            ac13 <= 24'd0;
            ac14 <= 24'd0;
            ac15 <= 24'd0;
            ac16 <= 24'd0;
            ac17 <= 24'd0;
            y <= 16'd0;
        end else begin
            ac0 <= 8'd3 * x + ac1;
            ac1 <= 8'd5 * x + ac2;
            ac2 <= 8'd7 * x + ac3;
            ac3 <= 8'd9 * x + ac4;
            ac4 <= 8'd11 * x + ac5;
            ac5 <= 8'd13 * x + ac6;
            ac6 <= 8'd15 * x + ac7;
            ac7 <= 8'd17 * x + ac8;
            ac8 <= 8'd19 * x + ac9;
            ac9 <= 8'd19 * x + ac10;
            ac10 <= 8'd17 * x + ac11;
            ac11 <= 8'd15 * x + ac12;
            ac12 <= 8'd13 * x + ac13;
            ac13 <= 8'd11 * x + ac14;
            ac14 <= 8'd9 * x + ac15;
            ac15 <= 8'd7 * x + ac16;
            ac16 <= 8'd5 * x + ac17;
            ac17 <= 8'd3 * x;
            y <= ac0[15:0];
        end
    end
endmodule