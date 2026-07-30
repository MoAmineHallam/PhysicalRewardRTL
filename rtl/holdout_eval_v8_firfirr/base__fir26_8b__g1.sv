module base__fir26_8b__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    localparam SAMPLE_RATE = 26;
    reg [7:0] delay_line[0:SAMPLE_RATE-1];
    reg [15:0] accumulator;
    integer i;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < SAMPLE_RATE; i = i + 1) begin
                delay_line[i] <= 8'h00;
            end
            accumulator <= 16'h0000;
            y <= 16'h0000;
        end
        else begin
            // Shift the delay line
            for (i = SAMPLE_RATE - 1; i > 0; i = i - 1) begin
                delay_line[i] <= delay_line[i-1];
            end
            // Add the new input sample to the delay line
            delay_line[0] <= x;
            // Calculate the output
            accumulator <= (3*delay_line[0]) + (5*delay_line[1]) + (7*delay_line[2]) + (9*delay_line[3]) +
                (11*delay_line[4]) + (13*delay_line[5]) + (15*delay_line[6]) + (17*delay_line[7]) +
                (19*delay_line[8]) + (21*delay_line[9]) + (23*delay_line[10]) + (25*delay_line[11]) +
                (27*delay_line[12]) + (27*delay_line[13]) + (25*delay_line[14]) + (23*delay_line[15]) +
                (21*delay_line[16]) + (19*delay_line[17]) + (17*delay_line[18]) + (15*delay_line[19]) +
                (13*delay_line[20]) + (11*delay_line[21]) + (9*delay_line[22]) + (7*delay_line[23]) +
                (5*delay_line[24]) + (3*delay_line[25]);
            // Output the low 16 bits of the accumulator
            y <= accumulator[15:0];
        end
    end

endmodule