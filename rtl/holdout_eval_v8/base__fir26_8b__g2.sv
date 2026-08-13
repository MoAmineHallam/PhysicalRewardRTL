module base__fir26_8b__g2 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    reg [7:0] reg_block [0:25];
    integer i;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 26; i = i + 1) begin
                reg_block[i] <= 8'h00;
            end
            y <= 16'h0000;
        end else begin
            y <= reg_block[25] * 3 + reg_block[24] * 5 + reg_block[23] * 7 + reg_block[22] * 9 + reg_block[21] * 11 + reg_block[20] * 13 + reg_block[19] * 15 + reg_block[18] * 17 + reg_block[17] * 19 + reg_block[16] * 21 + reg_block[15] * 23 + reg_block[14] * 25 + reg_block[13] * 27 + reg_block[12] * 27 + reg_block[11] * 25 + reg_block[10] * 23 + reg_block[9] * 21 + reg_block[8] * 19 + reg_block[7] * 17 + reg_block[6] * 15 + reg_block[5] * 13 + reg_block[4] * 11 + reg_block[3] * 9 + reg_block[2] * 7 + reg_block[1] * 5 + reg_block[0] * 3;
            for (i = 0; i < 25; i = i + 1) begin
                reg_block[i] <= reg_block[i+1];
            end
            reg_block[25] <= x;
        end
    end

endmodule