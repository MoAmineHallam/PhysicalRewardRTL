module grpo__fir6_8b__g6 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  xs [0:5];
    reg  [15:0] y2;
    reg  [15:0] y3;
    reg  [15:0] y4;
    reg  [15:0] y5;
    reg  [15:0] y6;
    wire [23:0] acc = 24'd3 * xs[0] + 24'd5 * xs[1] + 24'd7 * xs[2] + 24'd7 * xs[3] + 24'd5 * xs[4] + 24'd3 * xs[5];
    always @(posedge clk) begin
        if (!rst_n) begin
            for (int i = 0; i < 6; i = i + 1) xs[i] <= 8'd0;
            y <= 16'd0;
            y2 <= 16'd0;
            y3 <= 16'd0;
            y4 <= 16'd0;
            y5 <= 16'd0;
            y6 <= 16'd0;
        end else begin
            xs[0] <= x;
            xs[1] <= xs[0];
            xs[2] <= xs[1];
            xs[3] <= xs[2];
            xs[4] <= xs[3];
            xs[5] <= xs[4];
            y <= acc[15:0];
            y2 <= y;
            y3 <= y2;
            y4 <= y3;
            y5 <= y4;
            y6 <= y5;
        end
    end
endmodule