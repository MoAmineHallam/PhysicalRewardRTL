module grpo__fir10_8b__g5 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  xs [0:9];
    integer     i;
    reg  [15:0] y_reg;
    wire [7:0]  x0 = xs[0];
    wire [7:0]  x1 = xs[1];
    wire [7:0]  x2 = xs[2];
    wire [7:0]  x3 = xs[3];
    wire [7:0]  x4 = xs[4];
    wire [7:0]  x5 = xs[5];
    wire [7:0]  x6 = xs[6];
    wire [7:0]  x7 = xs[7];
    wire [7:0]  x8 = xs[8];
    wire [7:0]  x9 = xs[9];
    wire [15:0] acc = 8'd3 * x0 + 8'd5 * x1 + 8'd7 * x2 + 8'd9 * x3 + 8'd11 * x4 + 8'd11 * x5 + 8'd9 * x6 + 8'd7 * x7 + 8'd5 * x8 + 8'd3 * x9;
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 10; i = i + 1) xs[i] <= 8'd0;
            y_reg <= 16'd0;
        end else begin
            xs[0] <= x;
            for (i = 1; i < 10; i = i + 1) xs[i] <= xs[i-1];
            y_reg <= acc;
        end
        y <= y_reg;
    end
endmodule