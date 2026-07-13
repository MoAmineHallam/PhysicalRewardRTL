module sft__firr18__g2 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  xs [0:17];
    integer     i;
    reg  [23:0] acc;
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 18; i = i + 1) xs[i] <= 8'd0;
            acc <= 24'd0;
            y <= 16'd0;
        end else begin
            xs[0] <= x;
            for (i = 1; i < 18; i = i + 1) xs[i] <= xs[i-1];
            acc = 24'd1 * xs[0] + 24'd2 * xs[1] + 24'd3 * xs[2] + 24'd4 * xs[3] + 24'd5 * xs[4] + 24'd6 * xs[5] + 24'd7 * xs[6] + 24'd8 * xs[7] + 24'd9 * xs[8] + 24'd10 * xs[9] + 24'd11 * xs[10] + 24'd12 * xs[11] + 24'd13 * xs[12] + 24'd14 * xs[13] + 24'd15 * xs[14] + 24'd16 * xs[15] + 24'd17 * xs[16] + 24'd18 * xs[17];
            y <= acc[15:0];
        end
    end
endmodule