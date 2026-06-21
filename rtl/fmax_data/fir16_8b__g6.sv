module fir16_8b__g6 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [7:0] xs [0:15];
    reg [23:0] p [0:15];
    integer i;
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 16; i = i + 1) begin xs[i] <= 8'd0; p[i] <= 24'd0; end
            y <= 16'd0;
        end else begin
            xs[0] <= x;
            for (i = 1; i < 16; i = i + 1) xs[i] <= xs[i-1];
            p[0] <= 8'd3 * xs[0];
            p[1] <= 8'd7 * xs[1];
            p[2] <= 8'd12 * xs[2];
            p[3] <= 8'd19 * xs[3];
            p[4] <= 8'd27 * xs[4];
            p[5] <= 8'd34 * xs[5];
            p[6] <= 8'd40 * xs[6];
            p[7] <= 8'd43 * xs[7];
            p[8] <= 8'd43 * xs[8];
            p[9] <= 8'd40 * xs[9];
            p[10] <= 8'd34 * xs[10];
            p[11] <= 8'd27 * xs[11];
            p[12] <= 8'd19 * xs[12];
            p[13] <= 8'd12 * xs[13];
            p[14] <= 8'd7 * xs[14];
            p[15] <= 8'd3 * xs[15];
            y <= p[0] + p[1] + p[2] + p[3] + p[4] + p[5] + p[6] + p[7] + p[8] + p[9] + p[10] + p[11] + p[12] + p[13] + p[14] + p[15];
        end
    end
endmodule