module sft__fir6_8b__g6 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  xs [0:5];
    reg  [15:0] ys [0:5];
    integer     i;
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 6; i = i + 1) begin xs[i] <= 8'd0; ys[i] <= 16'd0; end
            y <= 16'd0;
        end else begin
            xs[0] <= x;
            ys[0] <= 8'd3 * xs[0] + 8'd5 * xs[1] + 8'd7 * xs[2] + 8'd7 * xs[3] + 8'd5 * xs[4] + 8'd3 * xs[5];
            for (i = 1; i < 6; i = i + 1) begin
                xs[i] <= xs[i-1];
                ys[i] <= ys[i-1];
            end
            y <= ys[5];
        end
    end
endmodule