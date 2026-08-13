module base__fir6_8b__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    reg [7:0] delay_line [0:5]; // A 6-element delay line
    reg [31:0] accumulator; // Accumulator for the sum of products

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            y <= 16'b0;
            accumulator <= 32'b0;
            for (int i = 0; i < 6; i = i + 1) begin
                delay_line[i] <= 8'b0;
            end
        end
        else begin
            // Shift the delay line
            delay_line[5] <= delay_line[4];
            delay_line[4] <= delay_line[3];
            delay_line[3] <= delay_line[2];
            delay_line[2] <= delay_line[1];
            delay_line[1] <= delay_line[0];
            delay_line[0] <= x;

            // Update the accumulator
            accumulator <= (delay_line[0] * 3) + (delay_line[1] * 5) + (delay_line[2] * 7) + (delay_line[3] * 7) + (delay_line[4] * 5) + (delay_line[5] * 3);

            // Output the low 16 bits of the accumulator
            y <= accumulator[15:0];
        end
    end

endmodule