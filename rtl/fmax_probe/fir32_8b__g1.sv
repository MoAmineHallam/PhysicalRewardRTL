module fir32_8b__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  delay [0:31];
    integer     i;
    reg  [23:0] acc;
    always @(*) acc = 8'd3 * delay[0] + 8'd5 * delay[1] + 8'd7 * delay[2] + 8'd9 * delay[3] + 8'd11 * delay[4] + 8'd13 * delay[5] + 8'd15 * delay[6] + 8'd17 * delay[7] + 8'd19 * delay[8] + 8'd21 * delay[9] + 8'd23 * delay[10] + 8'd25 * delay[11] + 8'd27 * delay[12] + 8'd29 * delay[13] + 8'd31 * delay[14] + 8'd33 * delay[15] + 8'd33 * delay[16] + 8'd31 * delay[17] + 8'd29 * delay[18] + 8'd27 * delay[19] + 8'd25 * delay[20] + 8'd23 * delay[21] + 8'd21 * delay[22] + 8'd19 * delay[23] + 8'd17 * delay[24] + 8'd15 * delay[25] + 8'd13 * delay[26] + 8'd11 * delay[27] + 8'd9 * delay[28] + 8'd7 * delay[29] + 8'd5 * delay[30] + 8'd3 * delay[31];
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 32; i = i + 1) delay[i] <= 8'd0;
            y <= 16'd0;
        end else begin
            delay[0] <= x;
            for (i = 1; i < 32; i = i + 1) delay[i] <= delay[i-1];
            y <= acc[15:0];
        end
    end
endmodule