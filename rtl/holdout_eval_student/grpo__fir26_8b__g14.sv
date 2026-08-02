module grpo__fir26_8b__g14 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [23:0] acc0, acc1, acc2, acc3, acc4, acc5, acc6, acc7, acc8, acc9, acc10, acc11, acc12, acc13, acc14, acc15, acc16, acc17, acc18, acc19, acc20, acc21, acc22, acc23, acc24, acc25;
    always @(posedge clk) begin
        if (!rst_n) begin
            acc0 <= 24'd0;
            acc1 <= 24'd0;
            acc2 <= 24'd0;
            acc3 <= 24'd0;
            acc4 <= 24'd0;
            acc5 <= 24'd0;
            acc6 <= 24'd0;
            acc7 <= 24'd0;
            acc8 <= 24'd0;
            acc9 <= 24'd0;
            acc10 <= 24'd0;
            acc11 <= 24'd0;
            acc12 <= 24'd0;
            acc13 <= 24'd0;
            acc14 <= 24'd0;
            acc15 <= 24'd0;
            acc16 <= 24'd0;
            acc17 <= 24'd0;
            acc18 <= 24'd0;
            acc19 <= 24'd0;
            acc20 <= 24'd0;
            acc21 <= 24'd0;
            acc22 <= 24'd0;
            acc23 <= 24'd0;
            acc24 <= 24'd0;
            acc25 <= 24'd0;
            y <= 16'd0;
        end else begin
            acc0 = 24'd3 * x + acc1;
            acc1 = 24'd5 * x + acc2;
            acc2 = 24'd7 * x + acc3;
            acc3 = 24'd9 * x + acc4;
            acc4 = 24'd11 * x + acc5;
            acc5 = 24'd13 * x + acc6;
            acc6 = 24'd15 * x + acc7;
            acc7 = 24'd17 * x + acc8;
            acc8 = 24'd19 * x + acc9;
            acc9 = 24'd21 * x + acc10;
            acc10 = 24'd23 * x + acc11;
            acc11 = 24'd25 * x + acc12;
            acc12 = 24'd27 * x + acc13;
            acc13 = 24'd27 * x + acc14;
            acc14 = 24'd25 * x + acc15;
            acc15 = 24'd23 * x + acc16;
            acc16 = 24'd21 * x + acc17;
            acc17 = 24'd19 * x + acc18;
            acc18 = 24'd17 * x + acc19;
            acc19 = 24'd15 * x + acc20;
            acc20 = 24'd13 * x + acc21;
            acc21 = 24'd11 * x + acc22;
            acc22 = 24'd9 * x + acc23;
            acc23 = 24'd7 * x + acc24;
            acc24 = 24'd5 * x + acc25;
            acc25 = 24'd3 * x;
            y <= acc0[15:0];
        end
    end
endmodule