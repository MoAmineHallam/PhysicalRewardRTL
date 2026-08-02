module sft__fir36_8b__g15 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [23:0] s0;
    reg [23:0] s1;
    reg [23:0] s2;
    reg [23:0] s3;
    reg [23:0] s4;
    reg [23:0] s5;
    reg [23:0] s6;
    reg [23:0] s7;
    reg [23:0] s8;
    reg [23:0] s9;
    reg [23:0] s10;
    reg [23:0] s11;
    reg [23:0] s12;
    reg [23:0] s13;
    reg [23:0] s14;
    reg [23:0] s15;
    reg [23:0] s16;
    reg [23:0] s17;
    reg [23:0] s18;
    reg [23:0] s19;
    reg [23:0] s20;
    reg [23:0] s21;
    reg [23:0] s22;
    reg [23:0] s23;
    reg [23:0] s24;
    reg [23:0] s25;
    reg [23:0] s26;
    reg [23:0] s27;
    reg [23:0] s28;
    reg [23:0] s29;
    reg [23:0] s30;
    reg [23:0] s31;
    reg [23:0] s32;
    reg [23:0] s33;
    reg [23:0] s34;
    reg [23:0] s35;
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
            s18 <= 24'd0;
            s19 <= 24'd0;
            s20 <= 24'd0;
            s21 <= 24'd0;
            s22 <= 24'd0;
            s23 <= 24'd0;
            s24 <= 24'd0;
            s25 <= 24'd0;
            s26 <= 24'd0;
            s27 <= 24'd0;
            s28 <= 24'd0;
            s29 <= 24'd0;
            s30 <= 24'd0;
            s31 <= 24'd0;
            s32 <= 24'd0;
            s33 <= 24'd0;
            s34 <= 24'd0;
            s35 <= 24'd0;
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
            s9 <= 8'd21 * x + s10;
            s10 <= 8'd23 * x + s11;
            s11 <= 8'd25 * x + s12;
            s12 <= 8'd27 * x + s13;
            s13 <= 8'd29 * x + s14;
            s14 <= 8'd31 * x + s15;
            s15 <= 8'd33 * x + s16;
            s16 <= 8'd35 * x + s17;
            s17 <= 8'd37 * x + s18;
            s18 <= 8'd37 * x + s19;
            s19 <= 8'd35 * x + s20;
            s20 <= 8'd33 * x + s21;
            s21 <= 8'd31 * x + s22;
            s22 <= 8'd29 * x + s23;
            s23 <= 8'd27 * x + s24;
            s24 <= 8'd25 * x + s25;
            s25 <= 8'd23 * x + s26;
            s26 <= 8'd21 * x + s27;
            s27 <= 8'd19 * x + s28;
            s28 <= 8'd17 * x + s29;
            s29 <= 8'd15 * x + s30;
            s30 <= 8'd13 * x + s31;
            s31 <= 8'd11 * x + s32;
            s32 <= 8'd9 * x + s33;
            s33 <= 8'd7 * x + s34;
            s34 <= 8'd5 * x + s35;
            s35 <= 8'd3 * x;
        end
    end
    always @(posedge clk) begin
        if (!rst_n) y <= 16'd0;
        else        y <= s0[15:0];
    end
endmodule