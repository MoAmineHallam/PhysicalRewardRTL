module base__fir18_8b__g5 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // 18-element delay line of past samples
    reg [7:0] delay_line [0:17];
    integer i;

    // Constants for the taps
    parameter TAP_0 = 3;
    parameter TAP_1 = 5;
    parameter TAP_2 = 7;
    parameter TAP_3 = 9;
    parameter TAP_4 = 11;
    parameter TAP_5 = 13;
    parameter TAP_6 = 15;
    parameter TAP_7 = 17;
    parameter TAP_8 = 19;
    parameter TAP_9 = 19;
    parameter TAP_10 = 17;
    parameter TAP_11 = 15;
    parameter TAP_12 = 13;
    parameter TAP_13 = 11;
    parameter TAP_14 = 9;
    parameter TAP_15 = 7;
    parameter TAP_16 = 5;
    parameter TAP_17 = 3;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear delay line and output to 0
            for (i = 0; i < 18; i = i + 1) begin
                delay_line[i] <= 8'd0;
            end
            y <= 16'd0;
        end else begin
            // Shift in new sample and calculate output
            for (i = 17; i > 0; i = i - 1) begin
                delay_line[i] <= delay_line[i-1];
            end
            delay_line[0] <= x;
            y <= (delay_line[0] * TAP_0 +
                  delay_line[1] * TAP_1 +
                  delay_line[2] * TAP_2 +
                  delay_line[3] * TAP_3 +
                  delay_line[4] * TAP_4 +
                  delay_line[5] * TAP_5 +
                  delay_line[6] * TAP_6 +
                  delay_line[7] * TAP_7 +
                  delay_line[8] * TAP_8 +
                  delay_line[9] * TAP_9 +
                  delay_line[10] * TAP_10 +
                  delay_line[11] * TAP_11 +
                  delay_line[12] * TAP_12 +
                  delay_line[13] * TAP_13 +
                  delay_line[14] * TAP_14 +
                  delay_line[15] * TAP_15 +
                  delay_line[16] * TAP_16 +
                  delay_line[17] * TAP_17);
        end
    end

endmodule