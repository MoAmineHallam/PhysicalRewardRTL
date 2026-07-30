module base__firr26__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    reg [7:0] delay_line [25:0]; // 26 elements, tap 0 is the newest
    integer i;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            y <= 0;
            for (i = 0; i < 26; i = i + 1) begin
                delay_line[i] <= 0;
            end
        end
        else begin
            // update delay line
            for (i = 25; i > 0; i = i - 1) begin
                delay_line[i] <= delay_line[i-1];
            end
            delay_line[0] <= x;

            // compute output
            y <= (1*delay_line[0] + 2*delay_line[1] + 3*delay_line[2] + 4*delay_line[3] + 5*delay_line[4] +
                  6*delay_line[5] + 7*delay_line[6] + 8*delay_line[7] + 9*delay_line[8] + 10*delay_line[9] +
                  11*delay_line[10] + 12*delay_line[11] + 13*delay_line[12] + 14*delay_line[13] + 15*delay_line[14] +
                  16*delay_line[15] + 17*delay_line[16] + 18*delay_line[17] + 19*delay_line[18] + 20*delay_line[19] +
                  21*delay_line[20] + 22*delay_line[21] + 23*delay_line[22] + 24*delay_line[23] + 25*delay_line[24] +
                  26*delay_line[25]);
        end
    end

endmodule