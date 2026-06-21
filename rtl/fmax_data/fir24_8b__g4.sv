module fir24_8b__g4 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [7:0] xs [0:23];
    integer i;
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 24; i = i + 1) begin xs[i] <= 8'd0; end
            y <= 16'd0;
        end else begin
            xs[0] <= x;
            for (i = 1; i < 24; i = i + 1) begin xs[i] <= xs[i-1]; end
            y <= xs[0] * 8'd3 + xs[1] * 8'd5 + xs[2] * 8'd7 + xs[3] * 8'd9 + xs[4] * 8'd11 + xs[5] * 8'd13 + xs[6] * 8'd15 + xs[7] * 8'd17 + xs[8] * 8'd19 + xs[9] * 8'd21 + xs[10] * 8'd23 + xs[11] * 8'd25 + xs[12] * 8'd25 + xs[13] * 8'd23 + xs[14] * 8'd21 + xs[15] * 8'd19 + xs[16] * 8'd17 + xs[17] * 8'd15 + xs[18] * 8'd13 + xs[19] * 8'd11 + xs[20] * 8'd9 + xs[21] * 8'd7 + xs[22] * 8'd5 + xs[23] * 8'd3;
        end
    end
endmodule