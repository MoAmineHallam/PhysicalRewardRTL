module sft__fir10_8b__g5 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  xs [0:9];
    integer     i;
    wire [23:0] acc = 8'd3 * xs[0] + 8'd5 * xs[1] + 8'd7 * xs[2] + 8'd9 * xs[3] + 8'd11 * xs[4] + 8'd11 * xs[5] + 8'd9 * xs[6] + 8'd7 * xs[7] + 8'd5 * xs[8] + 8'd3 * xs[9];
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 10; i = i + 1) xs[i] <= 8'd0;
            y <= 16'd0;
        end else begin
            xs[0] <= x;
            for (i = 1; i < 10; i = i + 1) xs[i] <= xs[i-1];
            y <= acc[15:0];
        end
    end
endmodule