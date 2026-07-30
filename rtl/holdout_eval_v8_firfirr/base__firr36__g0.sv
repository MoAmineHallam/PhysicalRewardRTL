module base__firr36__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

reg [7:0] tap [35:0];

always @ (posedge clk) begin
    if (!rst_n) begin
        y <= 0;
        for (int i = 0; i < 36; i = i + 1) begin
            tap[i] <= 8'h00;
        end
    end else begin
        y <= (tap[35] + 2*tap[34] + 3*tap[33] + 4*tap[32] + 5*tap[31] + 6*tap[30] + 7*tap[29] + 8*tap[28] + 9*tap[27] + 10*tap[26] + 11*tap[25] + 12*tap[24]
              + 13*tap[23] + 14*tap[22] + 15*tap[21] + 16*tap[20] + 17*tap[19] + 18*tap[18] + 19*tap[17] + 20*tap[16] + 21*tap[15] + 22*tap[14]
              + 23*tap[13] + 24*tap[12] + 25*tap[11] + 26*tap[10] + 27*tap[9] + 28*tap[8] + 29*tap[7] + 30*tap[6] + 31*tap[5]
              + 32*tap[4] + 33*tap[3] + 34*tap[2] + 35*tap[1] + 36*tap[0]);
        for (int i = 0; i < 35; i = i + 1) begin
            tap[i] <= tap[i+1];
        end
        tap[35] <= x;
    end
end

endmodule