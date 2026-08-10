module base__fir40_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    reg [7:0] delay_line [0:39];
    integer i;

    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 40; i = i + 1) begin
                delay_line[i] <= 8'd0;
            end
            y <= 16'd0;
        end
        else begin
            // Shift in new sample
            delay_line[0] <= x;
            // Compute new output
            y <= delay_line[39] * 9'd3 +
                 delay_line[38] * 9'd5 +
                 delay_line[37] * 9'd7 +
                 delay_line[36] * 9'd9 +
                 delay_line[35] * 9'd11 +
                 delay_line[34] * 9'd13 +
                 delay_line[33] * 9'd15 +
                 delay_line[32] * 9'd17 +
                 delay_line[31] * 9'd19 +
                 delay_line[30] * 9'd21 +
                 delay_line[29] * 9'd23 +
                 delay_line[28] * 9'd25 +
                 delay_line[27] * 9'd27 +
                 delay_line[26] * 9'd29 +
                 delay_line[25] * 9'd31 +
                 delay_line[24] * 9'd33 +
                 delay_line[23] * 9'd35 +
                 delay_line[22] * 9'd37 +
                 delay_line[21] * 9'd39 +
                 delay_line[20] * 9'd41 +
                 delay_line[19] * 9'd41 +
                 delay_line[18] * 9'd39 +
                 delay_line[17] * 9'd37 +
                 delay_line[16] * 9'd35 +
                 delay_line[15] * 9'd33 +
                 delay_line[14] * 9'd31 +
                 delay_line[13] * 9'd29 +
                 delay_line[12] * 9'd27 +
                 delay_line[11] * 9'd25 +
                 delay_line[10] * 9'd23 +
                 delay_line[9]  * 9'd21 +
                 delay_line[8]  * 9'd19 +
                 delay_line[7]  * 9'd17 +
                 delay_line[6]  * 9'd15 +
                 delay_line[5]  * 9'd13 +
                 delay_line[4]  * 9'd11 +
                 delay_line[3]  * 9'd9 +
                 delay_line[2]  * 9'd7 +
                 delay_line[1]  * 9'd5 +
                 delay_line[0]  * 9'd3;
                 
            // Shift out oldest sample
            for (i = 39; i > 0; i=i-1) begin
                delay_line[i] <= delay_line[i-1];
            end
        end
    end

endmodule