module sft__fir10_8b__g4 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [23:0] a1;
    reg  [23:0] a2;
    reg  [23:0] a3;
    reg  [23:0] a4;
    reg  [23:0] a5;
    reg  [23:0] a6;
    reg  [23:0] a7;
    reg  [23:0] a8;
    reg  [23:0] a9;
    reg  [23:0] a10;
    reg  [7:0] xd [0:9];
    always @(posedge clk) begin
        if (!rst_n) begin
            a1 <= 24'd0; a2 <= 24'd0; a3 <= 24'd0; a4 <= 24'd0; a5 <= 24'd0; a6 <= 24'd0; a7 <= 24'd0; a8 <= 24'd0; a9 <= 24'd0; a10 <= 24'd0;
            for (int i = 0; i < 10; i++) xd[i] <= 8'd0;
            y <= 16'd0;
        end else begin
            xd[0] <= x;
            for (int i = 1; i < 10; i++) xd[i] <= xd[i-1];
            a1 <= (8'd3 * xd[0]);
            a2 <= (8'd5 * xd[1]);
            a3 <= (8'd7 * xd[2]);
            a4 <= (8'd9 * xd[3]);
            a5 <= (8'd11 * xd[4]);
            a6 <= (8'd11 * xd[5]);
            a7 <= (8'd9 * xd[6]);
            a8 <= (8'd7 * xd[7]);
            a9 <= (8'd5 * xd[8]);
            a10 <= (8'd3 * xd[9]);
            y <= a1 + a2 + a3 + a4 + a5 + a6 + a7 + a8 + a9 + a10;
        end
    end
endmodule