// 32-tap direct-form FIR, 8-bit samples, PIPELINED: products registered in
// stage 1, summed in stage 2 -> shorter register-to-register path, higher Fmax.
// Functionally identical to the reference up to a fixed extra latency.
module fir32_8b__v1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  xs [0:31];
    reg  [15:0] p  [0:31];
    integer     i;
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 32; i = i + 1) begin xs[i] <= 8'd0; p[i] <= 16'd0; end
            y <= 16'd0;
        end else begin
            xs[0] <= x;
            for (i = 1; i < 32; i = i + 1) xs[i] <= xs[i-1];
            p[0] <= 8'd3 * xs[0];
            p[1] <= 8'd5 * xs[1];
            p[2] <= 8'd7 * xs[2];
            p[3] <= 8'd9 * xs[3];
            p[4] <= 8'd11 * xs[4];
            p[5] <= 8'd13 * xs[5];
            p[6] <= 8'd15 * xs[6];
            p[7] <= 8'd17 * xs[7];
            p[8] <= 8'd19 * xs[8];
            p[9] <= 8'd21 * xs[9];
            p[10] <= 8'd23 * xs[10];
            p[11] <= 8'd25 * xs[11];
            p[12] <= 8'd27 * xs[12];
            p[13] <= 8'd29 * xs[13];
            p[14] <= 8'd31 * xs[14];
            p[15] <= 8'd33 * xs[15];
            p[16] <= 8'd33 * xs[16];
            p[17] <= 8'd31 * xs[17];
            p[18] <= 8'd29 * xs[18];
            p[19] <= 8'd27 * xs[19];
            p[20] <= 8'd25 * xs[20];
            p[21] <= 8'd23 * xs[21];
            p[22] <= 8'd21 * xs[22];
            p[23] <= 8'd19 * xs[23];
            p[24] <= 8'd17 * xs[24];
            p[25] <= 8'd15 * xs[25];
            p[26] <= 8'd13 * xs[26];
            p[27] <= 8'd11 * xs[27];
            p[28] <= 8'd9 * xs[28];
            p[29] <= 8'd7 * xs[29];
            p[30] <= 8'd5 * xs[30];
            p[31] <= 8'd3 * xs[31];
            y <= p[0] + p[1] + p[2] + p[3] + p[4] + p[5] + p[6] + p[7] + p[8] + p[9] + p[10] + p[11] + p[12] + p[13] + p[14] + p[15] + p[16] + p[17] + p[18] + p[19] + p[20] + p[21] + p[22] + p[23] + p[24] + p[25] + p[26] + p[27] + p[28] + p[29] + p[30] + p[31];
        end
    end
endmodule
