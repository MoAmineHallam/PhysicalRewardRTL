module correctness_s1__fir30_v5_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  xs [0:29];
    integer     i;
    reg  [23:0] acc;
    always @(*) acc = 8'd44 * xs[0] + 8'd37 * xs[1] + 8'd25 * xs[2] + 8'd24 * xs[3] + 8'd58 * xs[4] + 8'd4 * xs[5] + 8'd24 * xs[6] + 8'd58 * xs[7] + 8'd23 * xs[8] + 8'd46 * xs[9] + 8'd25 * xs[10] + 8'd35 * xs[11] + 8'd40 * xs[12] + 8'd8 * xs[13] + 8'd33 * xs[14] + 8'd12 * xs[15] + 8'd18 * xs[16] + 8'd9 * xs[17] + 8'd63 * xs[18] + 8'd4 * xs[19] + 8'd1 * xs[20] + 8'd45 * xs[21] + 8'd21 * xs[22] + 8'd43 * xs[23] + 8'd25 * xs[24] + 8'd33 * xs[25] + 8'd4 * xs[26] + 8'd57 * xs[27] + 8'd44 * xs[28] + 8'd11 * xs[29];
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 30; i = i + 1) xs[i] <= 8'd0;
            y <= 16'd0;
        end else begin
            xs[0] <= x;
            for (i = 1; i < 30; i = i + 1) xs[i] <= xs[i-1];
            y <= acc[15:0];
        end
    end
endmodule
