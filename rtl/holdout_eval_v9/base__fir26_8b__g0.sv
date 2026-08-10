module base__fir26_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

reg [7:0] delay_line [0:25];
reg [15:0] acc;

integer i;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        acc <= 16'b0;
        for (i = 0; i < 26; i = i + 1) begin
            delay_line[i] <= 8'b0;
        end
    end else begin
        delay_line[0] <= x;
        for (i = 0; i < 25; i = i + 1) begin
            delay_line[i+1] <= delay_line[i];
        end

        acc <= (delay_line[0] * 3) + (delay_line[1] * 5) + (delay_line[2] * 7) + (delay_line[3] * 9) +
               (delay_line[4] * 11) + (delay_line[5] * 13) + (delay_line[6] * 15) + (delay_line[7] * 17) +
               (delay_line[8] * 19) + (delay_line[9] * 21) + (delay_line[10] * 23) + (delay_line[11] * 25) +
               (delay_line[12] * 27) + (delay_line[13] * 27) + (delay_line[14] * 25) + (delay_line[15] * 23) +
               (delay_line[16] * 21) + (delay_line[17] * 19) + (delay_line[18] * 17) + (delay_line[19] * 15) +
               (delay_line[20] * 13) + (delay_line[21] * 11) + (delay_line[22] * 9) + (delay_line[23] * 7) +
               (delay_line[24] * 5) + (delay_line[25] * 3);

        y <= acc[15:0];
    end
end

endmodule