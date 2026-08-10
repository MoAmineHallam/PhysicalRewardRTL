module step0__fir40_8b__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  xs [0:39];
    integer     i;
    reg  [23:0] acc;
    always @(*) acc = 8'd3 * xs[0] + 8'd5 * xs[1] + 8'd7 * xs[2] + 8'd9 * xs[3] + 8'd11 * xs[4] + 8'd13 * xs[5] + 8'd15 * xs[6] + 8'd17 * xs[7] + 8'd19 * xs[8] + 8'd21 * xs[9] + 8'd23 * xs[10] + 8'd25 * xs[11] + 8'd27 * xs[12] + 8'd29 * xs[13] + 8'd31 * xs[14] + 8'd33 * xs[15] + 8'd35 * xs[16] + 8'd37 * xs[17] + 8'd39 * xs[18] + 8'd41 * xs[19] + 8'd41 * xs[20] + 8'd39 * xs[21] + 8'd37 * xs[22] + 8'd35 * xs[23] + 8'd33 * xs[24] + 8'd31 * xs[25] + 8'd29 * xs[26] + 8'd27 * xs[27] + 8'd25 * xs[28] + 8'd23 * xs[29] + 8'd21 * xs[30] + 8'd19 * xs[31] + 8'd17 * xs[32] + 8'd15 * xs[33] + 8'd13 * xs[34] + 8'd11 * xs[35] + 8'd9 * xs[36] + 8'd7 * xs[37] + 8'd5 * xs[38] + 8'd3 * xs[39];
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 40; i = i + 1) xs[i] <= 8'd0;
            y <= 16'd0;
        end else begin
            xs[0] <= x;
            for (i = 1; i < 40; i = i + 1) xs[i] <= xs[i-1];
            y <= acc[15:0];
        end
    end
endmodule