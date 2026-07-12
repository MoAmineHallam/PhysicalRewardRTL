module sft__firr26__g5 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  xs [0:25];
    integer     i;
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 26; i = i + 1) xs[i] <= 8'd0;
            y <= 16'd0;
        end else begin
            xs[0] <= x;
            for (i = 1; i < 26; i = i + 1) xs[i] <= xs[i-1];
            y <= (((1 * xs[0]) + (2 * xs[1]) + (3 * xs[2]) + (4 * xs[3]) + (5 * xs[4]) + (6 * xs[5]) + (7 * xs[6]) + (8 * xs[7]) + (9 * xs[8]) + (10 * xs[9]) + (11 * xs[10]) + (12 * xs[11]) + (13 * xs[12]) + (14 * xs[13]) + (15 * xs[14]) + (16 * xs[15]) + (17 * xs[16]) + (18 * xs[17]) + (19 * xs[18]) + (20 * xs[19]) + (21 * xs[20]) + (22 * xs[21]) + (23 * xs[22]) + (24 * xs[23]) + (25 * xs[24]) + (26 * xs[25]))) & 16'hFFFF;
        end
    end
endmodule