module sft__firr10__g10 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  xs [0:9];
    reg  [15:0] ys [0:9];
    integer     i;
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 10; i = i + 1) begin xs[i] <= 8'd0; ys[i] <= 16'd0; end
            y <= 16'd0;
        end else begin
            xs[0] <= x;
            ys[0] <= (1 * xs[0]) + (2 * xs[1]) + (3 * xs[2]) + (4 * xs[3]) + (5 * xs[4]) + (6 * xs[5]) + (7 * xs[6]) + (8 * xs[7]) + (9 * xs[8]) + (10 * xs[9]);
            y <= ys[0];
            for (i = 1; i < 10; i = i + 1) begin
                xs[i] <= xs[i-1];
                ys[i] <= ys[i-1] + (i + 1) * xs[i];
            end
        end
    end
endmodule