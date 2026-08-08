module base__firr40__g0(input wire clk,
              input wire rst_n,
              input wire [7:0] x,
              output reg [15:0] y);

    reg [7:0] delay_line [0:39];
    reg [15:0] sum;
    integer i;

    always @(posedge clk, negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 40; i = i + 1) begin
                delay_line[i] <= 0;
            end
            sum <= 0;
            y <= 0;
        end else begin
            for (i = 38; i >= 0; i = i - 1) begin
                delay_line[i+1] <= delay_line[i];
            end
            delay_line[0] <= x;
            
            sum <= delay_line[39] * 40 + delay_line[38] * 39 + delay_line[37] * 38 + delay_line[36] * 37 + delay_line[35] * 36 + delay_line[34] * 35 + delay_line[33] * 34 + delay_line[32] * 33 + delay_line[31] * 32 + delay_line[30] * 31 + delay_line[29] * 30 + delay_line[28] * 29 + delay_line[27] * 28 + delay_line[26] * 27 + delay_line[25] * 26 + delay_line[24] * 25 + delay_line[23] * 24 + delay_line[22] * 23 + delay_line[21] * 22 + delay_line[20] * 21 + delay_line[19] * 20 + delay_line[18] * 19 + delay_line[17] * 18 + delay_line[16] * 17 + delay_line[15] * 16 + delay_line[14] * 15 + delay_line[13] * 14 + delay_line[12] * 13 + delay_line[11] * 12 + delay_line[10] * 11 + delay_line[9] * 10 + delay_line[8] * 9 + delay_line[7] * 8 + delay_line[6] * 7 + delay_line[5] * 6 + delay_line[4] * 5 + delay_line[3] * 4 + delay_line[2] * 3 + delay_line[1] * 2 + delay_line[0];

            y <= sum[15:0];
        end
    end
endmodule