module sft__firr18__g6 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  xs [0:17];
    reg  [15:0] s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12, s13, s14, s15, s16, s17;
    integer i;
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 18; i = i + 1) xs[i] <= 8'd0;
            y <= 16'd0;
        end else begin
            xs[0] <= x;
            for (i = 1; i < 18; i = i + 1) xs[i] <= xs[i-1];
            s0 <= 8'd1 * xs[0];
            s1 <= 8'd2 * xs[1];
            s2 <= 8'd3 * xs[2];
            s3 <= 8'd4 * xs[3];
            s4 <= 8'd5 * xs[4];
            s5 <= 8'd6 * xs[5];
            s6 <= 8'd7 * xs[6];
            s7 <= 8'd8 * xs[7];
            s8 <= 8'd9 * xs[8];
            s9 <= 8'd10 * xs[9];
            s10 <= 8'd11 * xs[10];
            s11 <= 8'd12 * xs[11];
            s12 <= 8'd13 * xs[12];
            s13 <= 8'd14 * xs[13];
            s14 <= 8'd15 * xs[14];
            s15 <= 8'd16 * xs[15];
            s16 <= 8'd17 * xs[16];
            s17 <= 8'd18 * xs[17];
            y <= s0 + s1 + s2 + s3 + s4 + s5 + s6 + s7 + s8 + s9 + s10 + s11 + s12 + s13 + s14 + s15 + s16 + s17;
        end
    end
endmodule