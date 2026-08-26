module sft__fir30_v5_8b__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  xs [0:29];
    reg  [15:0] p  [0:29];
    integer     i;
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 30; i = i + 1) begin xs[i] <= 8'd0; p[i] <= 16'd0; end
            y <= 16'd0;
        end else begin
            xs[0] <= x;
            for (i = 1; i < 30; i = i + 1) xs[i] <= xs[i-1];
            p[0] <= 8'd44 * xs[0];
            p[1] <= 8'd37 * xs[1];
            p[2] <= 8'd25 * xs[2];
            p[3] <= 8'd24 * xs[3];
            p[4] <= 8'd58 * xs[4];
            p[5] <= 8'd4 * xs[5];
            p[6] <= 8'd24 * xs[6];
            p[7] <= 8'd58 * xs[7];
            p[8] <= 8'd23 * xs[8];
            p[9] <= 8'd46 * xs[9];
            p[10] <= 8'd25 * xs[10];
            p[11] <= 8'd35 * xs[11];
            p[12] <= 8'd40 * xs[12];
            p[13] <= 8'd8 * xs[13];
            p[14] <= 8'd33 * xs[14];
            p[15] <= 8'd12 * xs[15];
            p[16] <= 8'd18 * xs[16];
            p[17] <= 8'd9 * xs[17];
            p[18] <= 8'd63 * xs[18];
            p[19] <= 8'd4 * xs[19];
            p[20] <= 8'd1 * xs[20];
            p[21] <= 8'd45 * xs[21];
            p[22] <= 8'd21 * xs[22];
            p[23] <= 8'd43 * xs[23];
            p[24] <= 8'd25 * xs[24];
            p[25] <= 8'd33 * xs[25];
            p[26] <= 8'd4 * xs[26];
            p[27] <= 8'd57 * xs[27];
            p[28] <= 8'd44 * xs[28];
            p[29] <= 8'd11 * xs[29];
            y <= p[0] + p[1] + p[2] + p[3] + p[4] + p[5] + p[6] + p[7] + p[8] + p[9] + p[10] + p[11] + p[12] + p[13] + p[14] + p[15] + p[16] + p[17] + p[18] + p[19] + p[20] + p[21] + p[22] + p[23] + p[24] + p[25] + p[26] + p[27] + p[28] + p[29];
        end
    end
endmodule
