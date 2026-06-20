module fir8_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  xs [0:7];
    wire [15:0] p0 = 16'd3 * xs[0];
    wire [15:0] p1 = 16'd5 * xs[1];
    wire [15:0] p2 = 16'd7 * xs[2];
    wire [15:0] p3 = 16'd9 * xs[3];
    wire [15:0] p4 = 16'd9 * xs[4];
    wire [15:0] p5 = 16'd7 * xs[5];
    wire [15:0] p6 = 16'd5 * xs[6];
    wire [15:0] p7 = 16'd3 * xs[7];
    wire [15:0] sum = p0 + p1 + p2 + p3 + p4 + p5 + p6 + p7;
    always @(posedge clk) begin
        if (!rst_n) begin
            for (int i = 0; i < 8; i = i + 1) xs[i] <= 8'd0;
            y <= 16'd0;
        end else begin
            xs[0] <= x;
            for (int i = 1; i < 8; i = i + 1) xs[i] <= xs[i-1];
            y <= sum;
        end
    end
endmodule