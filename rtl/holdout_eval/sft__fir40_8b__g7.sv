module sft__fir40_8b__g7 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  x_vals [0:39];
    integer     i;
    reg  [23:0] acc = 24'd0;
    always @(*) begin
        acc = 24'd0;
        acc = acc + 8'd3 * x_vals[0];
        acc = acc + 8'd5 * x_vals[1];
        acc = acc + 8'd7 * x_vals[2];
        acc = acc + 8'd9 * x_vals[3];
        acc = acc + 8'd11 * x_vals[4];
        acc = acc + 8'd13 * x_vals[5];
        acc = acc + 8'd15 * x_vals[6];
        acc = acc + 8'd17 * x_vals[7];
        acc = acc + 8'd19 * x_vals[8];
        acc = acc + 8'd21 * x_vals[9];
        acc = acc + 8'd23 * x_vals[10];
        acc = acc + 8'd25 * x_vals[11];
        acc = acc + 8'd27 * x_vals[12];
        acc = acc + 8'd29 * x_vals[13];
        acc = acc + 8'd31 * x_vals[14];
        acc = acc + 8'd33 * x_vals[15];
        acc = acc + 8'd35 * x_vals[16];
        acc = acc + 8'd37 * x_vals[17];
        acc = acc + 8'd39 * x_vals[18];
        acc = acc + 8'd41 * x_vals[19];
        acc = acc + 8'd41 * x_vals[20];
        acc = acc + 8'd39 * x_vals[21];
        acc = acc + 8'd37 * x_vals[22];
        acc = acc + 8'd35 * x_vals[23];
        acc = acc + 8'd33 * x_vals[24];
        acc = acc + 8'd31 * x_vals[25];
        acc = acc + 8'd29 * x_vals[26];
        acc = acc + 8'd27 * x_vals[27];
        acc = acc + 8'd25 * x_vals[28];
        acc = acc + 8'd23 * x_vals[29];
        acc = acc + 8'd21 * x_vals[30];
        acc = acc + 8'd19 * x_vals[31];
        acc = acc + 8'd17 * x_vals[32];
        acc = acc + 8'd15 * x_vals[33];
        acc = acc + 8'd13 * x_vals[34];
        acc = acc + 8'd11 * x_vals[35];
        acc = acc + 8'd9 * x_vals[36];
        acc = acc + 8'd7 * x_vals[37];
        acc = acc + 8'd5 * x_vals[38];
        acc = acc + 8'd3 * x_vals[39];
    end
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 40; i = i + 1) x_vals[i] <= 8'd0;
            y <= 16'd0;
        end else begin
            x_vals[0] <= x;
            for (i = 1; i < 40; i = i + 1) x_vals[i] <= x_vals[i-1];
            y <= acc[15:0];
        end
    end
endmodule