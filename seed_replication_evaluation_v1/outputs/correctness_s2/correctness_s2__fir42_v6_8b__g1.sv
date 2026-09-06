module correctness_s2__fir42_v6_8b__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  xs [0:41];
    integer     i;
    reg  [23:0] acc;
    always @(*) acc = 8'd52 * xs[0] + 8'd37 * xs[1] + 8'd42 * xs[2] + 8'd47 * xs[3] + 8'd1 * xs[4] + 8'd38 * xs[5] + 8'd28 * xs[6] + 8'd58 * xs[7] + 8'd54 * xs[8] + 8'd41 * xs[9] + 8'd4 * xs[10] + 8'd12 * xs[11] + 8'd23 * xs[12] + 8'd32 * xs[13] + 8'd50 * xs[14] + 8'd48 * xs[15] + 8'd17 * xs[16] + 8'd27 * xs[17] + 8'd13 * xs[18] + 8'd16 * xs[19] + 8'd14 * xs[20] + 8'd50 * xs[21] + 8'd4 * xs[22] + 8'd29 * xs[23] + 8'd8 * xs[24] + 8'd63 * xs[25] + 8'd24 * xs[26] + 8'd30 * xs[27] + 8'd20 * xs[28] + 8'd53 * xs[29] + 8'd25 * xs[30] + 8'd18 * xs[31] + 8'd5 * xs[32] + 8'd54 * xs[33] + 8'd58 * xs[34] + 8'd1 * xs[35] + 8'd29 * xs[36] + 8'd23 * xs[37] + 8'd14 * xs[38] + 8'd28 * xs[39] + 8'd60 * xs[40] + 8'd9 * xs[41];
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 42; i = i + 1) xs[i] <= 8'd0;
            y <= 16'd0;
        end else begin
            xs[0] <= x;
            for (i = 1; i < 42; i = i + 1) xs[i] <= xs[i-1];
            y <= acc [15:0];
        end
    end
endmodule
