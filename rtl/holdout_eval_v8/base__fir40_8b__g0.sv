module base__fir40_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    reg [7:0] delay_line [0:39];

    integer i;

    always @(posedge clk, negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 40; i = i + 1) begin
                delay_line[i] <= 0;
            end
            y <= 0;
        end
        else begin
            delay_line[0] <= x;
            for (i = 1; i < 40; i = i + 1) begin
                delay_line[i] <= delay_line[i-1];
            end
            y[15:0] <= (3*delay_line[0] + 5*delay_line[1] + 7*delay_line[2] + 9*delay_line[3] + 11*delay_line[4] + 13*delay_line[5] + 15*delay_line[6] + 17*delay_line[7] + 19*delay_line[8] + 21*delay_line[9] + 23*delay_line[10] + 25*delay_line[11] + 27*delay_line[12] + 29*delay_line[13] + 31*delay_line[14] + 33*delay_line[15] + 35*delay_line[16] + 37*delay_line[17] + 39*delay_line[18] + 41*delay_line[19] + 41*delay_line[20] + 39*delay_line[21] + 37*delay_line[22] + 35*delay_line[23] + 33*delay_line[24] + 31*delay_line[25] + 29*delay_line[26] + 27*delay_line[27] + 25*delay_line[28] + 23*delay_line[29] + 21*delay_line[30] + 19*delay_line[31] + 17*delay_line[32] + 15*delay_line[33] + 13*delay_line[34] + 11*delay_line[35] + 9*delay_line[36] + 7*delay_line[37] + 5*delay_line[38] + 3*delay_line[39]) & 16'hFFFF;
        end
    end
endmodule