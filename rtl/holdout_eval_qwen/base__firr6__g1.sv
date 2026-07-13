module base__firr6__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

// Internal register for the delay line
reg [7:0] taps [0:5];

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        // Reset all state to 0 when rst_n is active low
        y <= 0;
        taps[0] <= 0;
        taps[1] <= 0;
        taps[2] <= 0;
        taps[3] <= 0;
        taps[4] <= 0;
        taps[5] <= 0;
    end else begin
        // Shift the delay line
        taps[5] <= taps[4];
        taps[4] <= taps[3];
        taps[3] <= taps[2];
        taps[2] <= taps[1];
        taps[1] <= taps[0];
        taps[0] <= x;

        // Compute the filtered output
        y <= (taps[0] * 1) + (taps[1] * 2) + (taps[2] * 3) + 
             (taps[3] * 4) + (taps[4] * 5) + (taps[5] * 6);
    end
end

endmodule