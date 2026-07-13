module sft__fir40_8b__g7 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  xs [0:39];
    integer     i;
    reg  [23:0] acc;
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 40; i = i + 1) xs[i] <= 8'd0;
            acc <= 24'd0;
            y <= 16'd0;
        end else begin
            xs[0] <= x;
            for (i = 1; i < 40; i = i + 1) xs[i] <= xs[i-1];
            acc = 24'd3 * xs[0] + 24'd5 * xs[1] + 24'd7 * xs[2] + 24'd9 * xs[3] + 24'd11 * xs[4] + 24'd13 * xs[5] + 24'd15 * xs[6] + 24'd17 * xs[7] + 24'd19 * xs[8] + 24'd21 * xs[9] + 24'd23 * xs[10] + 24'd25 * xs[11] + 24'd27 * xs[12] + 24'd29 * xs[13] + 24'd31 * xs[14] + 24'd33 * xs[15] + 24'd35 * xs[16] + 24'd37 * xs[17] + 24'd39 * xs[18] + 24'd41 * xs[19] + 24'd41 * xs[20] + 24'd39 * xs[21] + 24'd37 * xs[22] + 24'd35 * xs[23] + 24'd33 * xs[24] + 24'd31 * xs[25] + 24'd29 * xs[26] + 24'd27 * xs[27] + 24'd25 * xs[28] + 24'd23 * xs[29] + 24'd21 * xs[30] + 24'd19 * xs[31] + 24'd17 * xs[32] + 24'd15 * xs[33] + 24'd13 * xs[34] + 24'd11 * xs[35] + 24'd9 * xs[36] + 24'd7 * xs[37] + 24'd5 * xs[38] + 24'd3 * xs[39];
            y <= acc[15:0];
        end
    end
endmodule