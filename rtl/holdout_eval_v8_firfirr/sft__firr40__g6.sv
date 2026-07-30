module sft__firr40__g6 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  mem [0:39];
    integer     i;
    reg  [23:0] acc;
    always @(*) acc = 8'd1 * mem[0] + 8'd2 * mem[1] + 8'd3 * mem[2] + 8'd4 * mem[3] + 8'd5 * mem[4] + 8'd6 * mem[5] + 8'd7 * mem[6] + 8'd8 * mem[7] + 8'd9 * mem[8] + 8'd10 * mem[9] + 8'd11 * mem[10] + 8'd12 * mem[11] + 8'd13 * mem[12] + 8'd14 * mem[13] + 8'd15 * mem[14] + 8'd16 * mem[15] + 8'd17 * mem[16] + 8'd18 * mem[17] + 8'd19 * mem[18] + 8'd20 * mem[19] + 8'd21 * mem[20] + 8'd22 * mem[21] + 8'd23 * mem[22] + 8'd24 * mem[23] + 8'd25 * mem[24] + 8'd26 * mem[25] + 8'd27 * mem[26] + 8'd28 * mem[27] + 8'd29 * mem[28] + 8'd30 * mem[29] + 8'd31 * mem[30] + 8'd32 * mem[31] + 8'd33 * mem[32] + 8'd34 * mem[33] + 8'd35 * mem[34] + 8'd36 * mem[35] + 8'd37 * mem[36] + 8'd38 * mem[37] + 8'd39 * mem[38] + 8'd40 * mem[39];
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 40; i = i + 1) mem[i] <= 8'd0;
            y <= 16'd0;
        end else begin
            mem[0] <= x;
            for (i = 1; i < 40; i = i + 1) mem[i] <= mem[i-1];
            y <= acc[15:0];
        end
    end
endmodule