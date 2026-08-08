module sft__fir26_8b__g3 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  mem [0:25];
    reg  [15:0] acc = 16'd0;
    integer     i;
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 26; i = i + 1) mem[i] <= 8'd0;
            acc <= 16'd0;
            y <= 16'd0;
        end else begin
            acc <= 16'd3 * mem[0] + 16'd5 * mem[1] + 16'd7 * mem[2] + 16'd9 * mem[3] + 16'd11 * mem[4] + 16'd13 * mem[5] + 16'd15 * mem[6] + 16'd17 * mem[7] + 16'd19 * mem[8] + 16'd21 * mem[9] + 16'd23 * mem[10] + 16'd25 * mem[11] + 16'd27 * mem[12] + 16'd27 * mem[13] + 16'd25 * mem[14] + 16'd23 * mem[15] + 16'd21 * mem[16] + 16'd19 * mem[17] + 16'd17 * mem[18] + 16'd15 * mem[19] + 16'd13 * mem[20] + 16'd11 * mem[21] + 16'd9 * mem[22] + 16'd7 * mem[23] + 16'd5 * mem[24] + 16'd3 * mem[25];
            for (i = 25; i > 0; i = i - 1) mem[i] <= mem[i - 1];
            mem[0] <= x;
            y <= acc;
        end
    end
endmodule