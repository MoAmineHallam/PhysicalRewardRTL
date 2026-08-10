module sft__fir18_8b__g5 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  xs [0:17];
    reg  [15:0] ys [0:17];
    integer     i;
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 18; i = i + 1) begin xs[i] <= 8'd0; ys[i] <= 16'd0; end
            y <= 16'd0;
        end else begin
            xs[0] <= x;
            for (i = 1; i < 18; i = i + 1) xs[i] <= xs[i-1];
            ys[0] <= 8'd3 * xs[0] + 8'd5 * xs[1] + 8'd7 * xs[2] + 8'd9 * xs[3] + 8'd11 * xs[4] + 8'd13 * xs[5] + 8'd15 * xs[6] + 8'd17 * xs[7] + 8'd19 * xs[8] + 8'd19 * xs[9] + 8'd17 * xs[10] + 8'd15 * xs[11] + 8'd13 * xs[12] + 8'd11 * xs[13] + 8'd9 * xs[14] + 8'd7 * xs[15] + 8'd5 * xs[16] + 8'd3 * xs[17];
            for (i = 1; i < 18; i = i + 1) ys[i] <= ys[i-1];
            y <= ys[17];
        end
    end
endmodule