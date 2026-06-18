// 24-tap direct-form FIR, 8-bit samples, unpipelined MAC cone (the long
// register-to-register path -> lower Fmax; pipeline it to go faster).
module fir24_8b__v0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  xs [0:23];
    integer     i;
    reg  [23:0] acc;
    always @(*) acc = 8'd3 * xs[0] + 8'd5 * xs[1] + 8'd7 * xs[2] + 8'd9 * xs[3] + 8'd11 * xs[4] + 8'd13 * xs[5] + 8'd15 * xs[6] + 8'd17 * xs[7] + 8'd19 * xs[8] + 8'd21 * xs[9] + 8'd23 * xs[10] + 8'd25 * xs[11] + 8'd25 * xs[12] + 8'd23 * xs[13] + 8'd21 * xs[14] + 8'd19 * xs[15] + 8'd17 * xs[16] + 8'd15 * xs[17] + 8'd13 * xs[18] + 8'd11 * xs[19] + 8'd9 * xs[20] + 8'd7 * xs[21] + 8'd5 * xs[22] + 8'd3 * xs[23];
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 24; i = i + 1) xs[i] <= 8'd0;
            y <= 16'd0;
        end else begin
            xs[0] <= x;
            for (i = 1; i < 24; i = i + 1) xs[i] <= xs[i-1];
            y <= acc[15:0];
        end
    end
endmodule
