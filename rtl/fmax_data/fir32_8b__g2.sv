module fir32_8b__g2 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [7:0] xs [0:31];
    integer i;
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 32; i = i + 1) xs[i] <= 8'd0;
            y <= 16'd0;
        end else begin
            xs[0] <= x;
            for (i = 1; i < 32; i = i + 1) xs[i] <= xs[i-1];
            y <= 8'd3 * xs[0] + 8'd5 * xs[1] + 8'd7 * xs[2] + 8'd9 * xs[3] + 8'd11 * xs[4] + 8'd13 * xs[5] + 8'd15 * xs[6] + 8'd17 * xs[7] + 8'd19 * xs[8] + 8'd21 * xs[9] + 8'd23 * xs[10] + 8'd25 * xs[11] + 8'd27 * xs[12] + 8'd29 * xs[13] + 8'd31 * xs[14] + 8'd33 * xs[15] + 8'd33 * xs[16] + 8'd31 * xs[17] + 8'd29 * xs[18] + 8'd27 * xs[19] + 8'd25 * xs[20] + 8'd23 * xs[21] + 8'd21 * xs[22] + 8'd19 * xs[23] + 8'd17 * xs[24] + 8'd15 * xs[25] + 8'd13 * xs[26] + 8'd11 * xs[27] + 8'd9 * xs[28] + 8'd7 * xs[29] + 8'd5 * xs[30] + 8'd3 * xs[31];
        end
    end
endmodule