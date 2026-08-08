module sft__fir26_8b__g3 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  xs [0:25];
    reg  [15:0] pp [0:25];
    integer     i;
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 26; i = i + 1) begin xs[i] <= 8'd0; pp[i] <= 16'd0; end
            y <= 16'd0;
        end else begin
            xs[0] <= x;
            for (i = 1; i < 26; i = i + 1) xs[i] <= xs[i-1];
            pp[0] <= 8'd3 * xs[0];
            pp[1] <= 8'd5 * xs[1];
            pp[2] <= 8'd7 * xs[2];
            pp[3] <= 8'd9 * xs[3];
            pp[4] <= 8'd11 * xs[4];
            pp[5] <= 8'd13 * xs[5];
            pp[6] <= 8'd15 * xs[6];
            pp[7] <= 8'd17 * xs[7];
            pp[8] <= 8'd19 * xs[8];
            pp[9] <= 8'd21 * xs[9];
            pp[10] <= 8'd23 * xs[10];
            pp[11] <= 8'd25 * xs[11];
            pp[12] <= 8'd27 * xs[12];
            pp[13] <= 8'd27 * xs[13];
            pp[14] <= 8'd25 * xs[14];
            pp[15] <= 8'd23 * xs[15];
            pp[16] <= 8'd21 * xs[16];
            pp[17] <= 8'd19 * xs[17];
            pp[18] <= 8'd17 * xs[18];
            pp[19] <= 8'd15 * xs[19];
            pp[20] <= 8'd13 * xs[20];
            pp[21] <= 8'd11 * xs[21];
            pp[22] <= 8'd9 * xs[22];
            pp[23] <= 8'd7 * xs[23];
            pp[24] <= 8'd5 * xs[24];
            pp[25] <= 8'd3 * xs[25];
            y <= pp[0] + pp[1] + pp[2] + pp[3] + pp[4] + pp[5] + pp[6] + pp[7] + pp[8] + pp[9] + pp[10] + pp[11] + pp[12] + pp[13] + pp[14] + pp[15] + pp[16] + pp[17] + pp[18] + pp[19] + pp[20] + pp[21] + pp[22] + pp[23] + pp[24] + pp[25];
        end
    end
endmodule