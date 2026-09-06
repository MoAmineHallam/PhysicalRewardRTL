module correctness_s2__fir26_v8_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  xs [0:25];
    integer     i;
    reg  [23:0] acc;
    always @(*) acc = 8'd3 * xs[0] + 8'd23 * xs[1] + 8'd2 * xs[2] + 8'd52 * xs[3] + 8'd52 * xs[4] + 8'd61 * xs[5] + 8'd47 * xs[6] + 8'd33 * xs[7] + 8'd40 * xs[8] + 8'd63 * xs[9] + 8'd56 * xs[10] + 8'd44 * xs[11] + 8'd17 * xs[12] + 8'd43 * xs[13] + 8'd13 * xs[14] + 8'd18 * xs[15] + 8'd48 * xs[16] + 8'd28 * xs[17] + 8'd18 * xs[18] + 8'd28 * xs[19] + 8'd23 * xs[20] + 8'd57 * xs[21] + 8'd21 * xs[22] + 8'd57 * xs[23] + 8'd44 * xs[24] + 8'd38 * xs[25];
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 26; i = i + 1) xs[i] <= 8'd0;
            y <= 16'd0;
        end else begin
            xs[0] <= x;
            for (i = 1; i < 26; i = i + 1) xs[i] <= xs[i-1];
            y <= acc[15:0];
        end
    end
endmodule
