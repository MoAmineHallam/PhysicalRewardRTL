module base__fir26_8b__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

reg [25:0] shift_reg [0:25]; // 26-element delay line
integer i;

always @(posedge clk) begin
    if (!rst_n) begin
        y <= 0;
        for (i = 0; i < 26; i = i + 1) begin
            shift_reg[i] <= 0;
        end
    end
    else begin
        shift_reg[0] <= x;
        for (i = 0; i < 25; i = i + 1) begin
            shift_reg[i+1] <= shift_reg[i];
        end
        y <= {3'b0, shift_reg[25][7:0]} * 3 +
             {3'b0, shift_reg[24][7:0]} * 5 +
             {3'b0, shift_reg[23][7:0]} * 7 +
             {3'b0, shift_reg[22][7:0]} * 9 +
             {3'b0, shift_reg[21][7:0]} * 11 +
             {3'b0, shift_reg[20][7:0]} * 13 +
             {3'b0, shift_reg[19][7:0]} * 15 +
             {3'b0, shift_reg[18][7:0]} * 17 +
             {3'b0, shift_reg[17][7:0]} * 19 +
             {3'b0, shift_reg[16][7:0]} * 21 +
             {3'b0, shift_reg[15][7:0]} * 23 +
             {3'b0, shift_reg[14][7:0]} * 25 +
             {3'b0, shift_reg[13][7:0]} * 27 +
             {3'b0, shift_reg[12][7:0]} * 27 +
             {3'b0, shift_reg[11][7:0]} * 25 +
             {3'b0, shift_reg[10][7:0]} * 23 +
             {3'b0, shift_reg[9][7:0]} * 21 +
             {3'b0, shift_reg[8][7:0]} * 19 +
             {3'b0, shift_reg[7][7:0]} * 17 +
             {3'b0, shift_reg[6][7:0]} * 15 +
             {3'b0, shift_reg[5][7:0]} * 13 +
             {3'b0, shift_reg[4][7:0]} * 11 +
             {3'b0, shift_reg[3][7:0]} * 9 +
             {3'b0, shift_reg[2][7:0]} * 7 +
             {3'b0, shift_reg[1][7:0]} * 5 +
             {3'b0, shift_reg[0][7:0]} * 3;
    end
end

endmodule