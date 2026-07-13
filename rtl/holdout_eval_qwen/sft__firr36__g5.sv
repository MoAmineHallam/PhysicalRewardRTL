module sft__firr36__g5 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  xs [0:35];
    integer     i;
    reg  [23:0] acc;
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 36; i = i + 1) xs[i] <= 8'd0;
            acc <= 24'd0;
            y <= 16'd0;
        end else begin
            xs[0] <= x;
            for (i = 1; i < 36; i = i + 1) xs[i] <= xs[i-1];
            acc = 24'd0;
            acc = acc + 24'd1 * xs[0];
            acc = acc + 24'd2 * xs[1];
            acc = acc + 24'd3 * xs[2];
            acc = acc + 24'd4 * xs[3];
            acc = acc + 24'd5 * xs[4];
            acc = acc + 24'd6 * xs[5];
            acc = acc + 24'd7 * xs[6];
            acc = acc + 24'd8 * xs[7];
            acc = acc + 24'd9 * xs[8];
            acc = acc + 24'd10 * xs[9];
            acc = acc + 24'd11 * xs[10];
            acc = acc + 24'd12 * xs[11];
            acc = acc + 24'd13 * xs[12];
            acc = acc + 24'd14 * xs[13];
            acc = acc + 24'd15 * xs[14];
            acc = acc + 24'd16 * xs[15];
            acc = acc + 24'd17 * xs[16];
            acc = acc + 24'd18 * xs[17];
            acc = acc + 24'd19 * xs[18];
            acc = acc + 24'd20 * xs[19];
            acc = acc + 24'd21 * xs[20];
            acc = acc + 24'd22 * xs[21];
            acc = acc + 24'd23 * xs[22];
            acc = acc + 24'd24 * xs[23];
            acc = acc + 24'd25 * xs[24];
            acc = acc + 24'd26 * xs[25];
            acc = acc + 24'd27 * xs[26];
            acc = acc + 24'd28 * xs[27];
            acc = acc + 24'd29 * xs[28];
            acc = acc + 24'd30 * xs[29];
            acc = acc + 24'd31 * xs[30];
            acc = acc + 24'd32 * xs[31];
            acc = acc + 24'd33 * xs[32];
            acc = acc + 24'd34 * xs[33];
            acc = acc + 24'd35 * xs[34];
            acc = acc + 24'd36 * xs[35];
            y <= acc[15:0];
        end
    end
endmodule