module apiplain__firr6__g5 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // 6-element delay line (samples stored as 8-bit values)
    reg [7:0] taps [0:5];  // tap[0] = newest sample, tap[5] = oldest

    integer k;
    reg [15:0] sum_temp;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear all taps and output
            for (k = 0; k < 6; k = k + 1) begin
                taps[k] <= 8'b0;
            end
            y <= 16'b0;
        end else begin
            // Shift delay line: new x becomes tap[0], previous samples move right
            taps[0] <= x;
            for (k = 1; k < 6; k = k + 1) begin
                taps[k] <= taps[k-1];
            end

            // Compute sum over k=0..5 of (k+1)*tap[k]
            sum_temp = 16'b0;
            for (k = 0; k < 6; k = k + 1) begin
                sum_temp = sum_temp + ((k + 1) * taps[k]);
            end

            // Output low 16 bits of the sum
            y <= sum_temp;
        end
    end

endmodule