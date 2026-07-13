module base__firr6__g2 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

reg [7:0] taps [0:5];  // Delay line for past samples

// Shift register logic for the delay line
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        taps[0] <= 8'b0;
        taps[1] <= 8'b0;
        taps[2] <= 8'b0;
        taps[3] <= 8'b0;
        taps[4] <= 8'b0;
        taps[5] <= 8'b0;
        y       <= 16'b0;
    end else begin
        taps[0] <= x;
        taps[1] <= taps[0];
        taps[2] <= taps[1];
        taps[3] <= taps[2];
        taps[4] <= taps[3];
        taps[5] <= taps[4];

        // Calculate the filtered output
        y <= (taps[0] * 1) + 
             (taps[1] * 2) + 
             (taps[2] * 3) + 
             (taps[3] * 4) + 
             (taps[4] * 5) + 
             (taps[5] * 6);
    end
end

endmodule