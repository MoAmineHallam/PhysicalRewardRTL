module base__fir10_8b__g3 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

reg [7:0] x_delay [0:9];
reg [15:0] y_accum;
integer i;

always @(posedge clk) begin
    if (!rst_n) begin
        y <= 0;
        y_accum <= 0;
        for (i = 0; i < 10; i = i + 1) begin
            x_delay[i] <= 0;
        end
    end
    else begin
        // Shift the delay line
        for (i = 9; i > 0; i = i - 1) begin
            x_delay[i] <= x_delay[i-1];
        end
        // Add the new sample
        x_delay[0] <= x;
        // Update the accumulator
        y_accum <= x_delay[0]*3 + x_delay[1]*5 + x_delay[2]*7 + x_delay[3]*9 + x_delay[4]*11 
                   + x_delay[5]*11 + x_delay[6]*9 + x_delay[7]*7 + x_delay[8]*5 + x_delay[9]*3;
        // Truncate the accumulator
        y <= y_accum[15:0];
    end
end

endmodule