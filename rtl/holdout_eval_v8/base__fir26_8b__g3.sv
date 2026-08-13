module base__fir26_8b__g3 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

reg [7:0] delay_line [25:0];
integer i;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        for (i = 0; i < 26; i = i + 1) begin
            delay_line[i] <= 0;
        end
        y <= 0;
    end
    else begin
        delay_line[0] <= x;
        for (i = 1; i < 26; i = i + 1) begin
            delay_line[i] <= delay_line[i-1];
        end
        y <= (3 * delay_line[0]) + (5 * delay_line[1]) + (7 * delay_line[2]) +
             (9 * delay_line[3]) + (11 * delay_line[4]) + (13 * delay_line[5]) +
             (15 * delay_line[6]) + (17 * delay_line[7]) + (19 * delay_line[8]) +
             (21 * delay_line[9]) + (23 * delay_line[10]) + (25 * delay_line[11]) +
             (27 * delay_line[12]) + (27 * delay_line[13]) + (25 * delay_line[14]) +
             (23 * delay_line[15]) + (21 * delay_line[16]) + (19 * delay_line[17]) +
             (17 * delay_line[18]) + (15 * delay_line[19]) + (13 * delay_line[20]) +
             (11 * delay_line[21]) + (9 * delay_line[22]) + (7 * delay_line[23]) +
             (5 * delay_line[24]) + (3 * delay_line[25]);
    end
end

endmodule