// 12-tap direct-form FIR, 8-bit samples, unpipelined MAC cone (the long
// register-to-register path -> lower Fmax; pipeline it to go faster).
module firr12__v0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  xs [0:11];
    integer     i;
    reg  [23:0] acc;
    always @(*) acc = 8'd1 * xs[0] + 8'd2 * xs[1] + 8'd3 * xs[2] + 8'd4 * xs[3] + 8'd5 * xs[4] + 8'd6 * xs[5] + 8'd7 * xs[6] + 8'd8 * xs[7] + 8'd9 * xs[8] + 8'd10 * xs[9] + 8'd11 * xs[10] + 8'd12 * xs[11];
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 12; i = i + 1) xs[i] <= 8'd0;
            y <= 16'd0;
        end else begin
            xs[0] <= x;
            for (i = 1; i < 12; i = i + 1) xs[i] <= xs[i-1];
            y <= acc[15:0];
        end
    end
endmodule
