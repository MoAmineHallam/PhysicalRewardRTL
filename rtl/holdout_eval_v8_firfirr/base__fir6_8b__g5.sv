module base__fir6_8b__g5 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    reg [7:0] delay_line [5:0];
    reg [15:0] acc;
    integer i;

    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 6; i = i + 1) begin
                delay_line[i] <= 8'h00;
            end
            acc <= 16'h0000;
            y <= 16'h0000;
        end
        else begin
            // Shift old samples into the delay line
            for (i = 5; i > 0; i = i - 1) begin
                delay_line[i] <= delay_line[i-1];
            end

            // Add new sample to the delay line
            delay_line[0] <= x;

            // Compute the accumulator
            acc <= (delay_line[0] * 8'h03) + 
                   (delay_line[1] * 8'h05) +
                   (delay_line[2] * 8'h07) +
                   (delay_line[3] * 8'h07) +
                   (delay_line[4] * 8'h05) +
                   (delay_line[5] * 8'h03);

            // Output the low 16 bits of the accumulator
            y <= acc[15:0];
        end
    end

endmodule