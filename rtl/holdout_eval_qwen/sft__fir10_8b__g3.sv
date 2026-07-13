module sft__fir10_8b__g3 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  xs [0:9];
    reg  [15:0] acc;
    integer     i;
    always @(*) acc = 16'd3 * xs[0] + 16'd5 * xs[1] + 16'd7 * xs[2] + 16'd9 * xs[3] + 16'd11 * xs[4] + 16'd11 * xs[5] + 16'd9 * xs[6] + 16'd7 * xs[7] + 16'd5 * xs[8] + 16'd3 * xs[9];
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 10; i = i + 1) xs[i] <= 8'd0;
            y <= 16'd0;
        end else begin
            xs[0] <= x;
            for (i = 1; i < 10; i = i + 1) xs[i] <= xs[i - 1];
            y <= acc;
        end
    end
endmodule