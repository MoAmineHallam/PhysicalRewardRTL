module correctness_s2__fir13_v6_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  xs [0:12];
    integer     i;
    reg  [23:0] acc;
    always @(*) acc = 8'd19 * xs[0] + 8'd28 * xs[1] + 8'd42 * xs[2] + 8'd41 * xs[3] + 8'd60 * xs[4] + 8'd8 * xs[5] + 8'd17 * xs[6] + 8'd9 * xs[7] + 8'd28 * xs[8] + 8'd42 * xs[9] + 8'd19 * xs[10] + 8'd44 * xs[11] + 8'd37 * xs[12];
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 13; i = i + 1) xs[i] <= 8'd0;
            y <= 16'd0;
        end else begin
            xs[0] <= x;
            for (i = 1; i < 13; i = i + 1) xs[i] <= xs[i-1];
            y <= acc[15:0];
        end
    end
endmodule
