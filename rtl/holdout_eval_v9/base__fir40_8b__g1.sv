module base__fir40_8b__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

reg [7:0] delay_line [39:0];
reg [15:0] acc;
reg [4:0] tap_count = 40;

always @(posedge clk, negedge rst_n) begin
    if (!rst_n) begin
        y <= 0;
        acc <= 0;
        tap_count <= 40;
        for (int i = 0; i < 40; i = i + 1) begin
            delay_line[i] <= 0;
        end
    end
    else begin
        delay_line[0] <= x;
        acc <= delay_line[0] * 3 + delay_line[1] * 5 + delay_line[2] * 7 + delay_line[3] * 9 +
               delay_line[4] * 11 + delay_line[5] * 13 + delay_line[6] * 15 + delay_line[7] * 17 +
               delay_line[8] * 19 + delay_line[9] * 21 + delay_line[10] * 23 + delay_line[11] * 25 +
               delay_line[12] * 27 + delay_line[13] * 29 + delay_line[14] * 31 + delay_line[15] * 33 +
               delay_line[16] * 35 + delay_line[17] * 37 + delay_line[18] * 39 + delay_line[19] * 41 +
               delay_line[20] * 41 + delay_line[21] * 39 + delay_line[22] * 37 + delay_line[23] * 35 +
               delay_line[24] * 33 + delay_line[25] * 31 + delay_line[26] * 29 + delay_line[27] * 27 +
               delay_line[28] * 25 + delay_line[29] * 23 + delay_line[30] * 21 + delay_line[31] * 19 +
               delay_line[32] * 17 + delay_line[33] * 15 + delay_line[34] * 13 + delay_line[35] * 11 +
               delay_line[36] * 9 + delay_line[37] * 7 + delay_line[38] * 5 + delay_line[39] * 3;
        y <= acc[15:0];

        for (int i = 1; i <= 39; i = i + 1) begin
            delay_line[i] <= delay_line[i - 1];
        end

        if (tap_count == 1) begin
            y <= acc;
        end
        else begin
            tap_count <= tap_count - 1;
        end
    end
end

endmodule