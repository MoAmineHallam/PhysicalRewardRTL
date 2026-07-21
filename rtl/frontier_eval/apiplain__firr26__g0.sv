module apiplain__firr26__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Delay line: 26 registers, each 8 bits wide
    reg [7:0] tap [0:25];
    integer k;
    reg [23:0] sum;  // wide enough to avoid overflow before truncation

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear all taps
            for (k = 0; k < 26; k = k + 1) begin
                tap[k] <= 8'd0;
            end
            y <= 16'd0;
        end else begin
            // Shift delay line: tap[0] gets new sample x,
            // tap[1] gets old tap[0], etc.
            tap[0] <= x;
            for (k = 1; k < 26; k = k + 1) begin
                tap[k] <= tap[k-1];
            end

            // Compute sum of (k+1)*tap[k]
            sum = 24'd0;
            for (k = 0; k < 26; k = k + 1) begin
                sum = sum + (k + 1) * tap[k];
            end

            // Register output: low 16 bits of the sum
            y <= sum[15:0];
        end
    end

endmodule