module grpo__firr40__g6 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  xs [0:39];
    reg  [15:0] y2;
    reg  [31:0] acc;
    reg  [15:0] y2a;
    integer i;
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 40; i = i + 1) xs[i] <= 8'd0;
            y2 <= 16'd0;
            acc <= 32'd0;
            y2a <= 16'd0;
            y <= 16'd0;
        end else begin
            xs[0] <= x;
            for (i = 1; i < 40; i = i + 1) xs[i] <= xs[i-1];
            acc <= (1 * xs[0]) + (2 * xs[1]) + (3 * xs[2]) + (4 * xs[3]) + (5 * xs[4]) + (6 * xs[5]) + (7 * xs[6]) + (8 * xs[7]) + (9 * xs[8]) + (10 * xs[9]) + (11 * xs[10]) + (12 * xs[11]) + (13 * xs[12]) + (14 * xs[13]) + (15 * xs[14]) + (16 * xs[15]) + (17 * xs[16]) + (18 * xs[17]) + (19 * xs[18]) + (20 * xs[19]) + (21 * xs[20]) + (22 * xs[21]) + (23 * xs[22]) + (24 * xs[23]) + (25 * xs[24]) + (26 * xs[25]) + (27 * xs[26]) + (28 * xs[27]) + (29 * xs[28]) + (30 * xs[29]) + (31 * xs[30]) + (32 * xs[31]) + (33 * xs[32]) + (34 * xs[33]) + (35 * xs[34]) + (36 * xs[35]) + (37 * xs[36]) + (38 * xs[37]) + (39 * xs[38]) + (40 * xs[39]);
            y2 <= acc[15:0];
            y2a <= y2;
            y <= y2a;
        end
    end
endmodule