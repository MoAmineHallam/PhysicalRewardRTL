module base__fir6_8b__g2 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

reg [7:0] delay_line [0:5];
reg [15:0] acc;

always @(posedge clk) begin
    if (!rst_n) begin
        y <= 16'b0;
        acc <= 16'b0;
        for (int i = 0; i < 6; i = i + 1) begin
            delay_line[i] <= 8'b0;
        end
    end else begin
        // Shift the new sample into the delay line
        delay_line[0] <= x;
        for (int i = 1; i < 6; i = i + 1) begin
            delay_line[i] <= delay_line[i-1];
        end

        // Update the accumulator
        acc <= (delay_line[0] * 3) +
               (delay_line[1] * 5) +
               (delay_line[2] * 7) +
               (delay_line[3] * 7) +
               (delay_line[4] * 5) +
               (delay_line[5] * 3);

        // Output the low 16 bits of the accumulator
        y <= acc;
    end
end

endmodule