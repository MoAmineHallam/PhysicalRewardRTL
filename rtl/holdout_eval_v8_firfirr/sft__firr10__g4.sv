module sft__firr10__g4 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  xs [0:9];
    integer     i;
    wire [15:0] a0 = 8'd1 * xs[0];
    wire [15:0] a1 = 8'd2 * xs[1];
    wire [15:0] a2 = 8'd3 * xs[2];
    wire [15:0] a3 = 8'd4 * xs[3];
    wire [15:0] a4 = 8'd5 * xs[4];
    wire [15:0] a5 = 8'd6 * xs[5];
    wire [15:0] a6 = 8'd7 * xs[6];
    wire [15:0] a7 = 8'd8 * xs[7];
    wire [15:0] a8 = 8'd9 * xs[8];
    wire [15:0] a9 = 8'd10 * xs[9];
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 10; i = i + 1) xs[i] <= 8'd0;
            y <= 16'd0;
        end else begin
            xs[0] <= x;
            for (i = 1; i < 10; i = i + 1) xs[i] <= xs[i-1];
            y <= a0 + a1 + a2 + a3 + a4 + a5 + a6 + a7 + a8 + a9;
        end
    end
endmodule