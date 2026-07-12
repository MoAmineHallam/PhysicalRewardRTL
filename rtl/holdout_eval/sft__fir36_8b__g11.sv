module sft__fir36_8b__g11 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  fx [0:35];
    integer     i;
    reg  [23:0] acc;
    always @(*) acc = 8'd3 * fx[0] + 8'd5 * fx[1] + 8'd7 * fx[2] + 8'd9 * fx[3] + 8'd11 * fx[4] + 8'd13 * fx[5] + 8'd15 * fx[6] + 8'd17 * fx[7] + 8'd19 * fx[8] + 8'd21 * fx[9] + 8'd23 * fx[10] + 8'd25 * fx[11] + 8'd27 * fx[12] + 8'd29 * fx[13] + 8'd31 * fx[14] + 8'd33 * fx[15] + 8'd35 * fx[16] + 8'd37 * fx[17] + 8'd37 * fx[18] + 8'd35 * fx[19] + 8'd33 * fx[20] + 8'd31 * fx[21] + 8'd29 * fx[22] + 8'd27 * fx[23] + 8'd25 * fx[24] + 8'd23 * fx[25] + 8'd21 * fx[26] + 8'd19 * fx[27] + 8'd17 * fx[28] + 8'd15 * fx[29] + 8'd13 * fx[30] + 8'd11 * fx[31] + 8'd9 * fx[32] + 8'd7 * fx[33] + 8'd5 * fx[34] + 8'd3 * fx[35];
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 36; i = i + 1) fx[i] <= 8'd0;
            y <= 16'd0;
        end else begin
            fx[0] <= x;
            for (i = 1; i < 36; i = i + 1) fx[i] <= fx[i-1];
            y <= acc[15:0];
        end
    end
endmodule