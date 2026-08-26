module sft__fir30_v5_8b__g4 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  xs0, xs1, xs2, xs3, xs4, xs5, xs6, xs7, xs8, xs9, xs10, xs11, xs12, xs13, xs14, xs15, xs16, xs17, xs18, xs19, xs20, xs21, xs22, xs23, xs24, xs25, xs26, xs27, xs28, xs29;
    wire [23:0] acc = 44*xs0 + 37*xs1 + 25*xs2 + 24*xs3 + 58*xs4 + 4*xs5 + 24*xs6 + 58*xs7 + 23*xs8 + 46*xs9 + 25*xs10 + 35*xs11 + 40*xs12 + 8*xs13 + 33*xs14 + 12*xs15 + 18*xs16 + 9*xs17 + 63*xs18 + 4*xs19 + 1*xs20 + 45*xs21 + 21*xs22 + 43*xs23 + 25*xs24 + 33*xs25 + 4*xs26 + 57*xs27 + 44*xs28 + 11*xs29;
    always @(posedge clk) begin
        if (!rst_n) begin
            y<=0; xs0<=0; xs1<=0; xs2<=0; xs3<=0; xs4<=0; xs5<=0; xs6<=0; xs7<=0; xs8<=0; xs9<=0; xs10<=0; xs11<=0; xs12<=0; xs13<=0; xs14<=0; xs15<=0; xs16<=0; xs17<=0; xs18<=0; xs19<=0; xs20<=0; xs21<=0; xs22<=0; xs23<=0; xs24<=0; xs25<=0; xs26<=0; xs27<=0; xs28<=0; xs29<=0;
        end else begin
            y <= acc[15:0];
            xs0 <= x;
            xs1 <= xs0;
            xs2 <= xs1;
            xs3 <= xs2;
            xs4 <= xs3;
            xs5 <= xs4;
            xs6 <= xs5;
            xs7 <= xs6;
            xs8 <= xs7;
            xs9 <= xs8;
            xs10 <= xs9;
            xs11 <= xs10;
            xs12 <= xs11;
            xs13 <= xs12;
            xs14 <= xs13;
            xs15 <= xs14;
            xs16 <= xs15;
            xs17 <= xs16;
            xs18 <= xs17;
            xs19 <= xs18;
            xs20 <= xs19;
            xs21 <= xs20;
            xs22 <= xs21;
            xs23 <= xs22;
            xs24 <= xs23;
            xs25 <= xs24;
            xs26 <= xs25;
            xs27 <= xs26;
            xs28 <= xs27;
            xs29 <= xs28;
        end
    end
endmodule
