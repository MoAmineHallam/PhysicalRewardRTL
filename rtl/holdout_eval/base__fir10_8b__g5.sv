module base__fir10_8b__g5 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    parameter DEPTH = 10;
    parameter WIDTH = 8;

    reg [WIDTH-1:0] delay [0:DEPTH-1];

    integer i;

    always @(posedge clk) begin
        if (!rst_n) begin
            y <= 0;
            for (i = 0; i < DEPTH; i = i + 1) begin
                delay[i] <= 0;
            end
        end
        else begin
            // Add new sample to the delay line
            delay[0] <= x;

            // Shift all previous samples in the delay line
            for (i = 1; i < DEPTH; i = i + 1) begin
                delay[i] <= delay[i-1];
            end

            // Calculate the product of the taps with the coefficients
            y[15:0] <= (delay[0] * 3) + (delay[1] * 5) + (delay[2] * 7) + (delay[3] * 9) + (delay[4] * 11) + (delay[5] * 11) + (delay[6] * 9) + (delay[7] * 7) + (delay[8] * 5) + (delay[9] * 3);
        end
    end
endmodule