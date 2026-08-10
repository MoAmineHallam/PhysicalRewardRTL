module base__fir36_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

reg [7:0] delay_line [0:35];
integer i;

always @ (posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        for (i = 0; i < 36; i = i + 1) begin
            delay_line[i] <= 8'b0;
        end
        y <= 16'b0;
    end
    else begin
        // shift input into delay line
        delay_line[0] <= x;
        for (i = 1; i < 36; i = i + 1) begin
            delay_line[i] <= delay_line[i-1];
        end

        // calculate output
        // tap coefficients: 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25, 27, 29, 31, 33, 35, 37, 37, 35, 33, 31, 29, 27, 25, 23, 21, 19, 17, 15, 13, 11, 9, 7, 5, 3
        y <= (3*delay_line[35]) + (5*delay_line[34]) + (7*delay_line[33]) + (9*delay_line[32]) + (11*delay_line[31]) + (13*delay_line[30]) + (15*delay_line[29]) + (17*delay_line[28]) + (19*delay_line[27]) + (21*delay_line[26]) + (23*delay_line[25]) + (25*delay_line[24]) + (27*delay_line[23]) + (29*delay_line[22]) + (31*delay_line[21]) + (33*delay_line[20]) + (35*delay_line[19]) + (37*delay_line[18]) + (37*delay_line[17]) + (35*delay_line[16]) + (33*delay_line[15]) + (31*delay_line[14]) + (29*delay_line[13]) + (27*delay_line[12]) + (25*delay_line[11]) + (23*delay_line[10]) + (21*delay_line[9]) + (19*delay_line[8]) + (17*delay_line[7]) + (15*delay_line[6]) + (13*delay_line[5]) + (11*delay_line[4]) + (9*delay_line[3]) + (7*delay_line[2]) + (5*delay_line[1]) + (3*delay_line[0]);
    end
end

endmodule