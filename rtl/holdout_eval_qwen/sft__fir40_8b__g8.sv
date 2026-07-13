module sft__fir40_8b__g8 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  xs [0:39];
    reg  [15:0] acc;
    integer     i;
    always @(*) acc = 16'd3 * xs[0] + 16'd5 * xs[1] + 16'd7 * xs[2] + 16'd9 * xs[3] + 16'd11 * xs[4] + 16'd13 * xs[5] + 16'd15 * xs[6] + 16'd17 * xs[7] + 16'd19 * xs[8] + 16'd21 * xs[9] + 16'd23 * xs[10] + 16'd25 * xs[11] + 16'd27 * xs[12] + 16'd29 * xs[13] + 16'd31 * xs[14] + 16'd33 * xs[15] + 16'd35 * xs[16] + 16'd37 * xs[17] + 16'd39 * xs[18] + 16'd41 * xs[19] + 16'd41 * xs[20] + 16'd39 * xs[21] + 16'd37 * xs[22] + 16'd35 * xs[23] + 16'd33 * xs[24] + 16'd31 * xs[25] + 16'd29 * xs[26] + 16'd27 * xs[27] + 16'd25 * xs[28] + 16'd23 * xs[29] + 16'd21 * xs[30] + 16'd19 * xs[31] + 16'd17 * xs[32] + 16'd15 * xs[33] + 16'd13 * xs[34] + 16'd11 * xs[35] + 16'd9 * xs[36] + 16'd7 * xs[37] + 16'd5 * xs[38] + 16'd3 * xs[39];
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 40; i = i + 1) xs[i] <= 8'd0;
            acc <= 16'd0;
            y <= 16'd0;
        end else begin
            xs[0] <= x;
            for (i = 1; i < 40; i = i + 1) xs[i] <= xs[i-1];
            y <= acc[15:0];
        end
    end
endmodule