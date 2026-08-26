module sft__fir30_v5_8b__g6 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  xs0, xs1, xs2, xs3, xs4, xs5, xs6, xs7, xs8, xs9, xs10, xs11, xs12, xs13, xs14, xs15, xs16, xs17, xs18, xs19, xs20, xs21, xs22, xs23, xs24, xs25, xs26, xs27, xs28, xs29;
    wire [23:0] acc = 44*xs0 + 37*xs1 + 25*xs2 + 24*xs3 + 58*xs4 + 4*xs5 + 24*xs6 + 58*xs7 + 23*xs8 + 46*xs9 + 25*xs10 + 35*xs11 + 40*xs12 + 8*xs13 + 33*xs14 + 12*xs15 + 18*xs16 + 9*xs17 + 63*xs18 + 4*xs19 + 1*xs20 + 45*xs21 + 21*xs22 + 43*xs23 + 25*xs24 + 33*xs25 + 4*xs26 + 57*xs27 + 44*xs28 + 11*xs29;
    always @(posedge clk) begin
        if (!rst_n) begin
            y <= 16'd0;
            xs0 <= 8'd0; xs1 <= 8'd0; xs2 <= 8'd0; xs3 <= 8'd0; xs4 <= 8'd0; xs5 <= 8'd0; xs6 <= 8'd0; xs7 <= 8'd0; xs8 <= 8'd0; xs9 <= 8'd0; xs10 <= 8'd0; xs11 <= 8'd0; xs12 <= 8'd0; xs13 <= 8'd0; xs14 <= 8'd0; xs15 <= 8'd0; xs16 <= 8'd0; xs17 <= 8'd0; xs18 <= 8'd0; xs19 <= 8'd0; xs20 <= 8'd0; xs21 <= 8'd0; xs22 <= 8'd0; xs23 <= 8'd0; xs24 <= 8'd0; xs25 <= 8'd0; xs26 <= 8'd0; xs27 <= 8'd0; xs28 <= 8'd0; xs29 <= 8'd0;
        end else begin
            y <= acc[15:0];
            xs0 <= x;
            xs1 <= xs0; xs2 <= xs1; xs3 <= xs2; xs4 <= xs3; xs5 <= xs4; xs6 <= xs5; xs7 <= xs6; xs8 <= xs7; xs9 <= xs8; xs10 <= xs9; xs11 <= xs10; xs12 <= xs11; xs13 <= xs12; xs14 <= xs13; xs15 <= xs14; xs16 <= xs15; xs17 <= xs16; xs18 <= xs17; xs19 <= xs18; xs20 <= xs19; xs21 <= xs20; xs22 <= xs21; xs23 <= xs22; xs24 <= xs23; xs25 <= xs24; xs26 <= xs25; xs27 <= xs26; xs28 <= xs27; xs29 <= xs28;
        end
    end
endmodule
