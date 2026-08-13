module base__fir26_8b__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    parameter Tap1 = 3;
    parameter Tap2 = 5;
    parameter Tap3 = 7;
    parameter Tap4 = 9;
    parameter Tap5 = 11;
    parameter Tap6 = 13;
    parameter Tap7 = 15;
    parameter Tap8 = 17;
    parameter Tap9 = 19;
    parameter Tap10 = 21;
    parameter Tap11 = 23;
    parameter Tap12 = 25;
    parameter Tap13 = 27;
    parameter Tap14 = 27;
    parameter Tap15 = 25;
    parameter Tap16 = 23;
    parameter Tap17 = 21;
    parameter Tap18 = 19;
    parameter Tap19 = 17;
    parameter Tap20 = 15;
    parameter Tap21 = 13;
    parameter Tap22 = 11;
    parameter Tap23 = 9;
    parameter Tap24 = 7;
    parameter Tap25 = 5;
    parameter Tap26 = 3;

    reg [7:0] delay_line_reg [25:0];
    reg [15:0] accumulator_reg;
    integer i;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            y <= 0;
            for (i = 0; i < 26; i = i + 1) begin
                delay_line_reg[i] <= 8'h0;
            end
            accumulator_reg <= 16'h0;
        end
        else begin
            delay_line_reg[0] <= x;
            for (i = 0; i < 25; i = i + 1) begin
                delay_line_reg[i+1] <= delay_line_reg[i];
            end
            accumulator_reg <= delay_line_reg[0] * Tap1 + delay_line_reg[1] * Tap2 + delay_line_reg[2] * Tap3 + delay_line_reg[3] * Tap4 +
                               delay_line_reg[4] * Tap5 + delay_line_reg[5] * Tap6 + delay_line_reg[6] * Tap7 + delay_line_reg[7] * Tap8 +
                               delay_line_reg[8] * Tap9 + delay_line_reg[9] * Tap10 + delay_line_reg[10] * Tap11 + delay_line_reg[11] * Tap12 +
                               delay_line_reg[12] * Tap13 + delay_line_reg[13] * Tap14 + delay_line_reg[14] * Tap15 + delay_line_reg[15] * Tap16 +
                               delay_line_reg[16] * Tap17 + delay_line_reg[17] * Tap18 + delay_line_reg[18] * Tap19 + delay_line_reg[19] * Tap20 +
                               delay_line_reg[20] * Tap21 + delay_line_reg[21] * Tap22 + delay_line_reg[22] * Tap23 + delay_line_reg[23] * Tap24 +
                               delay_line_reg[24] * Tap25 + delay_line_reg[25] * Tap26;
            y <= accumulator_reg[15:0];
        end
    end

endmodule