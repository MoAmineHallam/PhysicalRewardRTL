module base__fir26_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

reg [7:0] delay [25:0]; // 26-element delay line

integer i;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        y <= 0;
        for (i = 0; i < 26; i = i + 1) begin
            delay[i] <= 0;
        end
    end
    else begin
        for (i = 0; i < 25; i = i + 1) begin
            delay[i+1] <= delay[i];
        end
        delay[0] <= x;

        y <= (delay[0] * 3) + (delay[1] * 5) + (delay[2] * 7) + (delay[3] * 9) +
             (delay[4] * 11) + (delay[5] * 13) + (delay[6] * 15) + (delay[7] * 17) +
             (delay[8] * 19) + (delay[9] * 21) + (delay[10] * 23) + (delay[11] * 25) +
             (delay[12] * 27) + (delay[13] * 27) + (delay[14] * 25) + (delay[15] * 23) +
             (delay[16] * 21) + (delay[17] * 19) + (delay[18] * 17) + (delay[19] * 15) +
             (delay[20] * 13) + (delay[21] * 11) + (delay[22] * 9) + (delay[23] * 7) +
             (delay[24] * 5) + (delay[25] * 3);
    end
end

endmodule