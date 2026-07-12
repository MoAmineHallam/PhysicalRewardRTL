module base__fir10_8b__g2 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    parameter TAPS = 10;
    parameter WIDTH = 8;

    reg [WIDTH-1:0] x_shift_reg [0:TAPS-1];
    reg [WIDTH+3:0] mult_accumulator [0:TAPS-1];

    integer i;

    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < TAPS; i = i + 1) begin
                x_shift_reg[i] <= 0;
                mult_accumulator[i] <= 0;
            end
            y <= 0;
        end else begin
            //Shift in new sample
            x_shift_reg[0] <= x;
            for (i = 0; i < TAPS - 1; i = i + 1) begin
                x_shift_reg[i+1] <= x_shift_reg[i];
            end

            //Multiply and accumulate
            mult_accumulator[0] <= x_shift_reg[0] * 3;
            mult_accumulator[1] <= x_shift_reg[1] * 5;
            mult_accumulator[2] <= x_shift_reg[2] * 7;
            mult_accumulator[3] <= x_shift_reg[3] * 9;
            mult_accumulator[4] <= x_shift_reg[4] * 11;
            mult_accumulator[5] <= x_shift_reg[5] * 11;
            mult_accumulator[6] <= x_shift_reg[6] * 9;
            mult_accumulator[7] <= x_shift_reg[7] * 7;
            mult_accumulator[8] <= x_shift_reg[8] * 5;
            mult_accumulator[9] <= x_shift_reg[9] * 3;

            //Accumulate sum
            y <= mult_accumulator[0] + mult_accumulator[1] + mult_accumulator[2] + mult_accumulator[3] + mult_accumulator[4] + mult_accumulator[5] + mult_accumulator[6] + mult_accumulator[7] + mult_accumulator[8] + mult_accumulator[9];
        end
    end

endmodule