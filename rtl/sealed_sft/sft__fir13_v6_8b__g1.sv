module sft__fir13_v6_8b__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  xs [0:12];
    reg  [15:0] p  [0:12];
    integer     i;
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 13; i = i + 1) begin xs[i] <= 8'd0; p[i] <= 16'd0; end
            y <= 16'd0;
        end else begin
            xs[0] <= x;
            for (i = 1; i < 13; i = i + 1) xs[i] <= xs[i-1];
            p[0] <= 8'd19 * xs[0];
            p[1] <= 8'd28 * xs[1];
            p[2] <= 8'd42 * xs[2];
            p[3] <= 8'd41 * xs[3];
            p[4] <= 8'd60 * xs[4];
            p[5] <= 8'd8 * xs[5];
            p[6] <= 8'd17 * xs[6];
            p[7] <= 8'd9 * xs[7];
            p[8] <= 8'd28 * xs[8];
            p[9] <= 8'd42 * xs[9];
            p[10] <= 8'd19 * xs[10];
            p[11] <= 8'd44 * xs[11];
            p[12] <= 8'd37 * xs[12];
            y <= p[0] + p[1] + p[2] + p[3] + p[4] + p[5] + p[6] + p[7] + p[8] + p[9] + p[10] + p[11] + p[12];
        end
    end
endmodule
