module base__firr36__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

// Declare the delay line (36 elements)
reg [7:0] tap [0:35];

// Internal signal to hold the sum
reg [31:0] sum;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        // Reset the outputs and the delay line
        y <= 16'b0;
        foreach (tap[i]) begin
            tap[i] <= 8'b0;
        end
        sum <= 32'b0;
    end else begin
        // Shift the delay line
        for (int i = 34; i >= 0; i--) begin
            tap[i + 1] <= tap[i];
        end
        // Update the delay line with the new sample
        tap[0] <= x;

        // Compute the sum
        sum <= 32'b0;
        for (int k = 0; k < 36; k++) begin
            sum += (k + 1) * $signed(tap[k]);
        end

        // Assign the result to the output register
        y <= sum[15:0];
    end
end

endmodule