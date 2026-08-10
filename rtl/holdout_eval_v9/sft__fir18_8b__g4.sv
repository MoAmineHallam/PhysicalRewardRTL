module sft__fir18_8b__g4 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  mem0;
    reg  [7:0]  mem1;
    reg  [7:0]  mem2;
    reg  [7:0]  mem3;
    reg  [7:0]  mem4;
    reg  [7:0]  mem5;
    reg  [7:0]  mem6;
    reg  [7:0]  mem7;
    reg  [7:0]  mem8;
    reg  [7:0]  mem9;
    reg  [7:0]  mem10;
    reg  [7:0]  mem11;
    reg  [7:0]  mem12;
    reg  [7:0]  mem13;
    reg  [7:0]  mem14;
    reg  [7:0]  mem15;
    reg  [7:0]  mem16;
    reg  [7:0]  mem17;
    wire [23:0] acc = 8'd3 * mem0 + 8'd5 * mem1 + 8'd7 * mem2 + 8'd9 * mem3 + 8'd11 * mem4 + 8'd13 * mem5 + 8'd15 * mem6 + 8'd17 * mem7 + 8'd19 * mem8 + 8'd19 * mem9 + 8'd17 * mem10 + 8'd15 * mem11 + 8'd13 * mem12 + 8'd11 * mem13 + 8'd9 * mem14 + 8'd7 * mem15 + 8'd5 * mem16 + 8'd3 * mem17;
    always @(posedge clk) begin
        if (!rst_n) begin
            y <= 16'd0;
            mem0 <= 8'd0;
            mem1 <= 8'd0;
            mem2 <= 8'd0;
            mem3 <= 8'd0;
            mem4 <= 8'd0;
            mem5 <= 8'd0;
            mem6 <= 8'd0;
            mem7 <= 8'd0;
            mem8 <= 8'd0;
            mem9 <= 8'd0;
            mem10 <= 8'd0;
            mem11 <= 8'd0;
            mem12 <= 8'd0;
            mem13 <= 8'd0;
            mem14 <= 8'd0;
            mem15 <= 8'd0;
            mem16 <= 8'd0;
            mem17 <= 8'd0;
        end else begin
            y <= acc[15:0];
            mem0 <= x;
            mem1 <= mem0;
            mem2 <= mem1;
            mem3 <= mem2;
            mem4 <= mem3;
            mem5 <= mem4;
            mem6 <= mem5;
            mem7 <= mem6;
            mem8 <= mem7;
            mem9 <= mem8;
            mem10 <= mem9;
            mem11 <= mem10;
            mem12 <= mem11;
            mem13 <= mem12;
            mem14 <= mem13;
            mem15 <= mem14;
            mem16 <= mem15;
            mem17 <= mem16;
        end
    end
endmodule