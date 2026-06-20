module fir32_8b__g2 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  xd [0:31];
    integer     i;
    reg  [23:0] acc;
    always @(*) acc = 8'd3 * xd[0] + 8'd5 * xd[1] + 8'd7 * xd[2] + 8'd9 * xd[3] + 8'd11 * xd[4] + 8'd13 * xd[5] + 8'd15 * xd[6] + 8'd17 * xd[7] + 8'd19 * xd[8] + 8'd21 * xd[9] + 8'd23 * xd[10] + 8'd25 * xd[11] + 8'd27 * xd[12] + 8'd29 * xd[13] + 8'd31 * xd[14] + 8'd33 * xd[15] + 8'd33 * xd[16] + 8'd31 * xd[17] + 8'd29 * xd[18] + 8'd27 * xd[19] + 8'd25 * xd[20] + 8'd23 * xd[21] + 8'd21 * xd[22] + 8'd19 * xd[23] + 8'd17 * xd[24] + 8'd15 * xd[25] + 8'd13 * xd[26] + 8'd11 * xd[27] + 8'd9 * xd[28] + 8'd7 * xd[29] + 8'd5 * xd[30] + 8'd3 * xd[31];
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 32; i = i + 1) xd[i] <= 8'd0;
            y <= 16'd0;
        end else begin
            xd[0] <= x;
            for (i = 1; i < 32; i = i + 1) xd[i] <= xd[i-1];
            y <= acc[15:0];
        end
    end
endmodule