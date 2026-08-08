module base__firr36__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

reg [7:0] delay_line[35:0];
reg [15:0] sum;
integer k;

always @(posedge clk) begin
    if (!rst_n) begin
        for (k = 0; k < 36; k = k + 1) begin
            delay_line[k] <= 0;
        end
        sum <= 0;
        y <= 0;
    end
    else begin
        delay_line[0] <= x;
        sum <= (1 * delay_line[0]) + (2 * delay_line[1]) + (3 * delay_line[2]) + (4 * delay_line[3]) + (5 * delay_line[4]) + (6 * delay_line[5]) + (7 * delay_line[6]) + (8 * delay_line[7]) + (9 * delay_line[8]) + (10 * delay_line[9]) + (11 * delay_line[10]) + (12 * delay_line[11]) + (13 * delay_line[12]) + (14 * delay_line[13]) + (15 * delay_line[14]) + (16 * delay_line[15]) + (17 * delay_line[16]) + (18 * delay_line[17]) + (19 * delay_line[18]) + (20 * delay_line[19]) + (21 * delay_line[20]) + (22 * delay_line[21]) + (23 * delay_line[22]) + (24 * delay_line[23]) + (25 * delay_line[24]) + (26 * delay_line[25]) + (27 * delay_line[26]) + (28 * delay_line[27]) + (29 * delay_line[28]) + (30 * delay_line[29]) + (31 * delay_line[30]) + (32 * delay_line[31]) + (33 * delay_line[32]) + (34 * delay_line[33]) + (35 * delay_line[34]) + (36 * delay_line[35]);
        for (k = 35; k > 0; k = k - 1) begin
            delay_line[k] <= delay_line[k-1];
        end
        y <= sum[15:0];
    end
end

endmodule