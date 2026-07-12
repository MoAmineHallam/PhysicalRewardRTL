module sft__fir26_8b__g3 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [7:0] xs [0:25];
    integer i;
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 26; i = i + 1) xs[i] <= 8'd0;
            y <= 16'd0;
        end else begin
            xs[0] <= x;
            for (i = 1; i < 26; i = i + 1) xs[i] <= xs[i-1];
            y <= 16'd3 * xs[0] + 16'd5 * xs[1] + 16'd7 * xs[2] + 16'd9 * xs[3] + 16'd11 * xs[4] + 16'd13 * xs[5] + 16'd15 * xs[6] + 16'd17 * xs[7] + 16'd19 * xs[8] + 16'd21 * xs[9] + 16'd23 * xs[10] + 16'd25 * xs[11] + 16'd27 * xs[12] + 16'd27 * xs[13] + 16'd25 * xs[14] + 16'd23 * xs[15] + 16'd21 * xs[16] + 16'd19 * xs[17] + 16'd17 * xs[18] + 16'd15 * xs[19] + 16'd13 * xs[20] + 16'd11 * xs[21] + 16'd9 * xs[22] + 16'd7 * xs[23] + 16'd5 * xs[24] + 16'd3 * xs[25];
        end
    end
endmodule