module correctness_s2__fir30_v5_8b__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  ys [0:29];
    integer     i;
    reg  [23:0] acc;
    always @(*) acc = 8'd44 * ys[0] + 8'd37 * ys[1] + 8'd25 * ys[2] + 8'd24 * ys[3] + 8'd58 * ys[4] + 8'd4 * ys[5] + 8'd24 * ys[6] + 8'd58 * ys[7] + 8'd23 * ys[8] + 8'd46 * ys[9] + 8'd25 * ys[10] + 8'd35 * ys[11] + 8'd40 * ys[12] + 8'd8 * ys[13] + 8'd33 * ys[14] + 8'd12 * ys[15] + 8'd18 * ys[16] + 8'd9 * ys[17] + 8'd63 * ys[18] + 8'd4 * ys[19] + 8'd1 * ys[20] + 8'd45 * ys[21] + 8'd21 * ys[22] + 8'd43 * ys[23] + 8'd25 * ys[24] + 8'd33 * ys[25] + 8'd4 * ys[26] + 8'd57 * ys[27] + 8'd44 * ys[28] + 8'd11 * ys[29];
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 30; i = i + 1) ys[i] <= 8'd0;
            y <= 16'd0;
        end else begin
            ys[0] <= x;
            for (i = 1; i < 30; i = i + 1) ys[i] <= ys[i-1];
            y <= acc[15:0];
        end
    end
endmodule
