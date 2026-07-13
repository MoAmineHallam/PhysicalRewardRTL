module base__firr6__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

reg [7:0] taps [5:0]; // Delay line for 6 taps

// Combinational logic to calculate the output y
always @(*) begin
    reg [31:0] acc; // Accumulator to hold the result of the dot product
    integer i;

    acc = 0;
    for (i = 0; i < 6; i = i + 1) begin
        acc = acc + (taps[i] * (i + 1));
    end

    // Assign the lower 16 bits of the accumulator to y
    y = acc[15:0];
end

// Sequential logic to update the delay line
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        // Clear all state to 0 on !rst_n
        y <= 0;
        taps[0] <= 0;
        taps[1] <= 0;
        taps[2] <= 0;
        taps[3] <= 0;
        taps[4] <= 0;
        taps[5] <= 0;
    end else begin
        // Update the delay line
        taps[5] <= taps[4];
        taps[4] <= taps[3];
        taps[3] <= taps[2];
        taps[2] <= taps[1];
        taps[1] <= taps[0];
        taps[0] <= x;
    end
end

endmodule