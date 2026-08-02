module grpo__fir10_8b__g1 (
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
    always @(posedge clk) begin
        if (!rst_n) begin
            a0 <= 24'b0;
            a1 <= 24'b0;
            a2 <= 24'b0;
            a3 <= 24'b0;
            a4 <= 24'b0;
            a5 <= 24'b0;
            a6 <= 24'b0;
            a7 <= 24'b0;
            a8 <= 24'b0;
            a9 <= 24'b0;
            y <= 16'b0;
        end else begin
            a0 <= (3 * x + a1) & 24'b1111111111111111;
            a1 <= (5 * x + a2) & 24'b1111111111111111;
            a2 <= (7 * x + a3) & 24'b1111111111111111;
            a3 <= (9 * x + a4) & 24'b1111111111111111;
            a4 <= (11 * x + a5) & 24'b1111111111111111;
            a5 <= (11 * x + a6) & 24'b1111111111111111;
            a6 <= (9 * x + a7) & 24'b1111111111111111;
            a7 <= (7 * x + a8) & 24'b1111111111111111;
            a8 <= (5 * x + a9) & 24'b1111111111111111;
            a9 <= (3 * x) & 24'b1111111111111111;
            y <= a0[15:0];
        end
    end
endmodule