module sft__fir42_v6_8b__g8 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  xs [0:41];
    wire [23:0] acc = 24'd52 * xs[0] + 24'd37 * xs[1] + 24'd42 * xs[2] + 24'd47 * xs[3] + 24'd1 * xs[4] + 24'd38 * xs[5] + 24'd28 * xs[6] + 24'd58 * xs[7] + 24'd54 * xs[8] + 24'd41 * xs[9] + 24'd4 * xs[10] + 24'd12 * xs[11] + 24'd23 * xs[12] + 24'd32 * xs[13] + 24'd50 * xs[14] + 24'd48 * xs[15] + 24'd17 * xs[16] + 24'd27 * xs[17] + 24'd13 * xs[18] + 24'd16 * xs[19] + 24'd14 * xs[20] + 24'd50 * xs[21] + 24'd4 * xs[22] + 24'd29 * xs[23] + 24'd8 * xs[24] + 24'd63 * xs[25] + 24'd24 * xs[26] + 24'd30 * xs[27] + 24'd20 * xs[28] + 24'd53 * xs[29] + 24'd25 * xs[30] + 24'd18 * xs[31] + 24'd5 * xs[32] + 24'd54 * xs[33] + 24'd58 * xs[34] + 24'd1 * xs[35] + 24'd29 * xs[36] + 24'd23 * xs[37] + 24'd14 * xs[38] + 24'd28 * xs[39] + 24'd60 * xs[40] + 24'd9 * xs[41];
    always @(posedge clk) begin
        if (!rst_n) begin
            for (int i = 0; i < 42; i = i + 1) xs[i] <= 8'd0;
            y <= 16'd0;
        end else begin
            xs[0] <= x;
            for (int i = 1; i < 42; i = i + 1) xs[i] <= xs[i-1];
            y <= acc[15:0];
        end
    end
endmodule
