module sft__firr20_v6__g3 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  xs [0:19];
    integer     i;
    reg  [23:0] acc;
    always @(*) acc = 24'd0 + 4*1*xs[0] + 4*2*xs[1] + 4*3*xs[2] + 4*4*xs[3] + 4*5*xs[4] + 4*6*xs[5] + 4*7*xs[6] + 4*8*xs[7] + 4*9*xs[8] + 4*10*xs[9] + 4*11*xs[10] + 4*12*xs[11] + 4*13*xs[12] + 4*14*xs[13] + 4*15*xs[14] + 4*16*xs[15] + 4*17*xs[16] + 4*18*xs[17] + 4*19*xs[18] + 4*20*xs[19];
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
