module correctness_s1__firr20_v6__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  xs [0:19];
    integer     i;
    reg  [23:0] acc;
    always @(*) acc = 8'd4 * xs[0] + 8'd8 * xs[1] + 8'd12 * xs[2] + 8'd16 * xs[3] + 8'd20 * xs[4] + 8'd24 * xs[5] + 8'd28 * xs[6] + 8'd32 * xs[7] + 8'd36 * xs[8] + 8'd40 * xs[9] + 8'd44 * xs[10] + 8'd48 * xs[11] + 8'd52 * xs[12] + 8'd56 * xs[13] + 8'd60 * xs[14] + 8'd64 * xs[15] + 8'd68 * xs[16] + 8'd72 * xs[17] + 8'd76 * xs[18] + 8'd80 * xs[19];
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 20; i = i + 1) xs[i] <= 8'd0;
            y <= 16'd0;
        end else begin
            xs[0] <= x;
            for (i = 1; i < 20; i = i + 1) xs[i] <= xs[i-1];
            y <= acc[15:0];
        end
    end
endmodule
