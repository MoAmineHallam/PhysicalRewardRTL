module sft__firr10__g5 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  xs [0:9];
    integer     i;
    reg  [15:0] y2;
    reg  [15:0] y3;
    reg  [15:0] y4;
    reg  [15:0] y5;
    reg  [15:0] y6;
    reg  [15:0] y7;
    reg  [15:0] y8;
    reg  [15:0] y9;
    reg  [15:0] y10;
    wire [23:0] acc = 8'd1 * xs[0] + 8'd2 * xs[1] + 8'd3 * xs[2] + 8'd4 * xs[3] + 8'd5 * xs[4] + 8'd6 * xs[5] + 8'd7 * xs[6] + 8'd8 * xs[7] + 8'd9 * xs[8] + 8'd10 * xs[9];
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 10; i = i + 1) xs[i] <= 8'd0;
            y <= 16'd0;
            y2 <= 16'd0;
            y3 <= 16'd0;
            y4 <= 16'd0;
            y5 <= 16'd0;
            y6 <= 16'd0;
            y7 <= 16'd0;
            y8 <= 16'd0;
            y9 <= 16'd0;
            y10 <= 16'd0;
        end else begin
            xs[0] <= x;
            for (i = 1; i < 10; i = i + 1) xs[i] <= xs[i-1];
            y <= acc[15:0];
            y2 <= (8'd1 * xs[1] + acc[23:16]) & 16'hFFFF;
            y3 <= (8'd1 * xs[2] + 8'd2 * xs[1] + acc[23:16]) & 16'hFFFF;
            y4 <= (8'd1 * xs[3] + 8'd2 * xs[2] + 8'd3 * xs[1] + acc[23:16]) & 16'hFFFF;
            y5 <= (8'd1 * xs[4] + 8'd2 * xs[3] + 8'd3 * xs[2] + 8'd4 * xs[1] + acc[23:16]) & 16'hFFFF;
            y6 <= (8'd1 * xs[5] + 8'd2 * xs[4] + 8'd3 * xs[3] + 8'd4 * xs[2] + 8'd5 * xs[1] + acc[23:16]) & 16'hFFFF;
            y7 <= (8'd1 * xs[6] + 8'd2 * xs[5] + 8'd3 * xs[4] + 8'd4 * xs[3] + 8'd5 * xs[2] + 8'd6 * xs[1] + acc[23:16]) & 16'hFFFF;
            y8 <= (8'd1 * xs[7] + 8'd2 * xs[6] + 8'd3 * xs[5] + 8'd4 * xs[4] + 8'd5 * xs[3] + 8'd6 * xs[2] + 8'd7 * xs[1] + acc[23:16]) & 16'hFFFF;
            y9 <= (8'd1 * xs[8] + 8'd2 * xs[7] + 8'd3 * xs[6] + 8'd4 * xs[5] + 8'd5 * xs[4] + 8'd6 * xs[3] + 8'd7 * xs[2] + 8'd8 * xs[1] + acc[23:16]) & 16'hFFFF;
            y10 <= (8'd1 * xs[9] + 8'd2 * xs[8] + 8'd3 * xs[7] + 8'd4 * xs[6] + 8'd5 * xs[5] + 8'd6 * xs[4] + 8'd7 * xs[3] + 8'd8 * xs[2] + 8'd9 * xs[1] + acc[23:16]) & 16'hFFFF;
        end
    end
endmodule