module sft__fir34_v1_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  xs [0:33];
    reg  [15:0] p  [0:33];
    integer     i;
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 34; i = i + 1) begin xs[i] <= 8'd0; p[i] <= 16'd0; end
            y <= 16'd0;
        end else begin
            xs[0] <= x;
            for (i = 1; i < 34; i = i + 1) xs[i] <= xs[i-1];
            p[0] <= 8'd59 * xs[0];
            p[1] <= 8'd41 * xs[1];
            p[2] <= 8'd24 * xs[2];
            p[3] <= 8'd13 * xs[3];
            p[4] <= 8'd56 * xs[4];
            p[5] <= 8'd5 * xs[5];
            p[6] <= 8'd31 * xs[6];
            p[7] <= 8'd61 * xs[7];
            p[8] <= 8'd44 * xs[8];
            p[9] <= 8'd42 * xs[9];
            p[10] <= 8'd13 * xs[10];
            p[11] <= 8'd1 * xs[11];
            p[12] <= 8'd7 * xs[12];
            p[13] <= 8'd58 * xs[13];
            p[14] <= 8'd21 * xs[14];
            p[15] <= 8'd7 * xs[15];
            p[16] <= 8'd19 * xs[16];
            p[17] <= 8'd28 * xs[17];
            p[18] <= 8'd23 * xs[18];
            p[19] <= 8'd26 * xs[19];
            p[20] <= 8'd39 * xs[20];
            p[21] <= 8'd33 * xs[21];
            p[22] <= 8'd5 * xs[22];
            p[23] <= 8'd57 * xs[23];
            p[24] <= 8'd28 * xs[24];
            p[25] <= 8'd11 * xs[25];
            p[26] <= 8'd18 * xs[26];
            p[27] <= 8'd34 * xs[27];
            p[28] <= 8'd5 * xs[28];
            p[29] <= 8'd11 * xs[29];
            p[30] <= 8'd53 * xs[30];
            p[31] <= 8'd14 * xs[31];
            p[32] <= 8'd1 * xs[32];
            p[33] <= 8'd48 * xs[33];
            y <= p[0] + p[1] + p[2] + p[3] + p[4] + p[5] + p[6] + p[7] + p[8] + p[9] + p[10] + p[11] + p[12] + p[13] + p[14] + p[15] + p[16] + p[17] + p[18] + p[19] + p[20] + p[21] + p[22] + p[23] + p[24] + p[25] + p[26] + p[27] + p[28] + p[29] + p[30] + p[31] + p[32] + p[33];
        end
    end
endmodule
