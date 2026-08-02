module sft__fir18_8b__g15 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [23:0] s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12, s13, s14, s15, s16, s17;
    always @(posedge clk) begin
        if (!rst_n) begin
            s0 <= 24'd0;
            s1 <= 24'd0;
            s2 <= 24'd0;
            s3 <= 24'd0;
            s4 <= 24'd0;
            s5 <= 24'd0;
            s6 <= 24'd0;
            s7 <= 24'd0;
            s8 <= 24'd0;
            s9 <= 24'd0;
            s10 <= 24'd0;
            s11 <= 24'd0;
            s12 <= 24'd0;
            s13 <= 24'd0;
            s14 <= 24'd0;
            s15 <= 24'd0;
            s16 <= 24'd0;
            s17 <= 24'd0;
            y <= 16'd0;
        end else begin
            s0 <= 8'd3 * x + s1;
            s1 <= 8'd5 * x + s2;
            s2 <= 8'd7 * x + s3;
            s3 <= 8'd9 * x + s4;
            s4 <= 8'd11 * x + s5;
            s5 <= 8'd13 * x + s6;
            s6 <= 8'd15 * x + s7;
            s7 <= 8'd17 * x + s8;
            s8 <= 8'd19 * x + s9;
            s9 <= 8'd19 * x + s10;
            s10 <= 8'd17 * x + s11;
            s11 <= 8'd15 * x + s12;
            s12 <= 8'd13 * x + s13;
            s13 <= 8'd11 * x + s14;
            s14 <= 8'd9 * x + s15;
            s15 <= 8'd7 * x + s16;
            s16 <= 8'd5 * x + s17;
            s17 <= 8'd3 * x;
            y <= s0[15:0];
        end
    end
endmodule