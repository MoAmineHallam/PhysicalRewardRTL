module fir32_8b__g3 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  mem [0:31];
    integer     i;
    reg  [23:0] acc;
    always @(*) acc = 8'd3 * mem[0] + 8'd5 * mem[1] + 8'd7 * mem[2] + 8'd9 * mem[3] + 8'd11 * mem[4] + 8'd13 * mem[5] + 8'd15 * mem[6] + 8'd17 * mem[7] + 8'd19 * mem[8] + 8'd21 * mem[9] + 8'd23 * mem[10] + 8'd25 * mem[11] + 8'd27 * mem[12] + 8'd29 * mem[13] + 8'd31 * mem[14] + 8'd33 * mem[15] + 8'd33 * mem[16] + 8'd31 * mem[17] + 8'd29 * mem[18] + 8'd27 * mem[19] + 8'd25 * mem[20] + 8'd23 * mem[21] + 8'd21 * mem[22] + 8'd19 * mem[23] + 8'd17 * mem[24] + 8'd15 * mem[25] + 8'd13 * mem[26] + 8'd11 * mem[27] + 8'd9 * mem[28] + 8'd7 * mem[29] + 8'd5 * mem[30] + 8'd3 * mem[31];
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 32; i = i + 1) mem[i] <= 8'd0;
            y <= 16'd0;
        end else begin
            mem[0] <= x;
            for (i = 1; i < 32; i = i + 1) mem[i] <= mem[i-1];
            y <= acc[15:0];
        end
    end
endmodule