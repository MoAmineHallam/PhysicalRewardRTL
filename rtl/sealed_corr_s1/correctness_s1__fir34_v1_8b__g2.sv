module correctness_s1__fir34_v1_8b__g2 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  xs [0:33];
    integer     i;
    reg  [23:0] acc;
    always @(*) acc = 8'd59 * xs[0] + 8'd41 * xs[1] + 8'd24 * xs[2] + 8'd13 * xs[3] + 8'd56 * xs[4] + 8'd5 * xs[5] + 8'd31 * xs[6] + 8'd61 * xs[7] + 8'd44 * xs[8] + 8'd42 * xs[9] + 8'd13 * xs[10] + 8'd1 * xs[11] + 8'd7 * xs[12] + 8'd58 * xs[13] + 8'd21 * xs[14] + 8'd7 * xs[15] + 8'd19 * xs[16] + 8'd28 * xs[17] + 8'd23 * xs[18] + 8'd26 * xs[19] + 8'd39 * xs[20] + 8'd33 * xs[21] + 8'd5 * xs[22] + 8'd57 * xs[23] + 8'd28 * xs[24] + 8'd11 * xs[25] + 8'd18 * xs[26] + 8'd34 * xs[27] + 8'd5 * xs[28] + 8'd11 * xs[29] + 8'd53 * xs[30] + 8'd14 * xs[31] + 8'd1 * xs[32] + 8'd48 * xs[33];
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 34; i = i + 1) xs[i] <= 8'd0;
            y <= 16'd0;
        end else begin
            xs[0] <= x;
            for (i = 1; i < 34; i = i + 1) xs[i] <= xs[i-1];
            y <= acc[15:0];
        end
    end
endmodule
