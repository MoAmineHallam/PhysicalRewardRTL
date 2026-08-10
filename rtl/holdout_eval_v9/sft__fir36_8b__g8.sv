module sft__fir36_8b__g8 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [7:0] xs [0:35];
    reg [15:0] prod [0:35];
    integer i;
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 36; i = i + 1) begin xs[i] <= 8'd0; prod[i] <= 16'd0; end
            y <= 16'd0;
        end else begin
            xs[0] <= x;
            for (i = 1; i < 36; i = i + 1) xs[i] <= xs[i-1];
            prod[0] <= 8'd3 * xs[0];
            prod[1] <= 8'd5 * xs[1];
            prod[2] <= 8'd7 * xs[2];
            prod[3] <= 8'd9 * xs[3];
            prod[4] <= 8'd11 * xs[4];
            prod[5] <= 8'd13 * xs[5];
            prod[6] <= 8'd15 * xs[6];
            prod[7] <= 8'd17 * xs[7];
            prod[8] <= 8'd19 * xs[8];
            prod[9] <= 8'd21 * xs[9];
            prod[10] <= 8'd23 * xs[10];
            prod[11] <= 8'd25 * xs[11];
            prod[12] <= 8'd27 * xs[12];
            prod[13] <= 8'd29 * xs[13];
            prod[14] <= 8'd31 * xs[14];
            prod[15] <= 8'd33 * xs[15];
            prod[16] <= 8'd35 * xs[16];
            prod[17] <= 8'd37 * xs[17];
            prod[18] <= 8'd37 * xs[18];
            prod[19] <= 8'd35 * xs[19];
            prod[20] <= 8'd33 * xs[20];
            prod[21] <= 8'd31 * xs[21];
            prod[22] <= 8'd29 * xs[22];
            prod[23] <= 8'd27 * xs[23];
            prod[24] <= 8'd25 * xs[24];
            prod[25] <= 8'd23 * xs[25];
            prod[26] <= 8'd21 * xs[26];
            prod[27] <= 8'd19 * xs[27];
            prod[28] <= 8'd17 * xs[28];
            prod[29] <= 8'd15 * xs[29];
            prod[30] <= 8'd13 * xs[30];
            prod[31] <= 8'd11 * xs[31];
            prod[32] <= 8'd9 * xs[32];
            prod[33] <= 8'd7 * xs[33];
            prod[34] <= 8'd5 * xs[34];
            prod[35] <= 8'd3 * xs[35];
            y <= prod[0] + prod[1] + prod[2] + prod[3] + prod[4] + prod[5] + prod[6] + prod[7] + prod[8] + prod[9] + prod[10] + prod[11] + prod[12] + prod[13] + prod[14] + prod[15] + prod[16] + prod[17] + prod[18] + prod[19] + prod[20] + prod[21] + prod[22] + prod[23] + prod[24] + prod[25] + prod[26] + prod[27] + prod[28] + prod[29] + prod[30] + prod[31] + prod[32] + prod[33] + prod[34] + prod[35];
        end
    end
endmodule