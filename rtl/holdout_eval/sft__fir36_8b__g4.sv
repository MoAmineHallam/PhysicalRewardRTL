module sft__fir36_8b__g4 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [7:0] delay [0:35];
    integer i;
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 36; i = i + 1) delay[i] <= 8'd0;
            y <= 16'd0;
        end else begin
            delay[0] <= x;
            for (i = 1; i < 36; i = i + 1) delay[i] <= delay[i-1];
            y <= 16'd3 * delay[0] + 16'd5 * delay[1] + 16'd7 * delay[2] + 16'd9 * delay[3] + 16'd11 * delay[4] + 16'd13 * delay[5] + 16'd15 * delay[6] + 16'd17 * delay[7] + 16'd19 * delay[8] + 16'd21 * delay[9] + 16'd23 * delay[10] + 16'd25 * delay[11] + 16'd27 * delay[12] + 16'd29 * delay[13] + 16'd31 * delay[14] + 16'd33 * delay[15] + 16'd35 * delay[16] + 16'd37 * delay[17] + 16'd37 * delay[18] + 16'd35 * delay[19] + 16'd33 * delay[20] + 16'd31 * delay[21] + 16'd29 * delay[22] + 16'd27 * delay[23] + 16'd25 * delay[24] + 16'd23 * delay[25] + 16'd21 * delay[26] + 16'd19 * delay[27] + 16'd17 * delay[28] + 16'd15 * delay[29] + 16'd13 * delay[30] + 16'd11 * delay[31] + 16'd9 * delay[32] + 16'd7 * delay[33] + 16'd5 * delay[34] + 16'd3 * delay[35];
        end
    end
endmodule