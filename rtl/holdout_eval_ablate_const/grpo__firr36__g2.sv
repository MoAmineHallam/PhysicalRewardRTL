module grpo__firr36__g2 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  xs [0:35];
    integer     i;
    reg  [23:0] acc;
    always @(*) acc = 8'd1 * xs[0] + 8'd2 * xs[1] + 8'd3 * xs[2] + 8'd4 * xs[3] + 8'd5 * xs[4] + 8'd6 * xs[5] + 8'd7 * xs[6] + 8'd8 * xs[7] + 8'd9 * xs[8] + 8'd10 * xs[9] + 8'd11 * xs[10] + 8'd12 * xs[11] + 8'd13 * xs[12] + 8'd14 * xs[13] + 8'd15 * xs[14] + 8'd16 * xs[15] + 8'd17 * xs[16] + 8'd18 * xs[17] + 8'd19 * xs[18] + 8'd20 * xs[19] + 8'd21 * xs[20] + 8'd22 * xs[21] + 8'd23 * xs[22] + 8'd24 * xs[23] + 8'd25 * xs[24] + 8'd26 * xs[25] + 8'd27 * xs[26] + 8'd28 * xs[27] + 8'd29 * xs[28] + 8'd30 * xs[29] + 8'd31 * xs[30] + 8'd32 * xs[31] + 8'd33 * xs[32] + 8'd34 * xs[33] + 8'd35 * xs[34] + 8'd36 * xs[35];
    always @(posedge clk) begin
        if (!rst_n) begin
            for(i = 0; i < 36; i = i + 1) xs[i] <= 8'd0;
            y <= 16'd0;
        end else begin
            xs[0] <= x;
            for(i = 1; i < 36; i = i + 1) xs[i] <= xs[i-1];
            y <= acc[15:0];
        end
    end
endmodule