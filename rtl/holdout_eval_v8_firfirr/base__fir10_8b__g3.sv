module base__fir10_8b__g3 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    reg [7:0] delay_line [0:9]; // Delay line of size 10
    integer i;

    always @(posedge clk) begin
        if (!rst_n) begin
            y <= 0; // Reset state
            for (i = 0; i < 10; i = i + 1) begin
                delay_line[i] <= 0; // Clear delay line
            end
        end
        else begin
            y <= (delay_line[9] * 3) + (delay_line[8] * 5) + (delay_line[7] * 7) + (delay_line[6] * 9) + (delay_line[5] * 11) + (delay_line[4] * 11) + (delay_line[3] * 9) + (delay_line[2] * 7) + (delay_line[1] * 5) + (delay_line[0] * 3); // Calculate 16-bit output
            for (i = 9; i > 0; i = i - 1) begin
                delay_line[i] <= delay_line[i-1]; // Shift delay line
            end
            delay_line[0] <= x; // Put new input into delay line
        end
    end

endmodule