module apiplain__firr40__g6 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // 40-element delay line (tap 0 = newest sample)
    reg [7:0] delay_line [0:39];
    integer i;

    // Sum accumulator (wide enough to avoid overflow before truncation)
    // Maximum coefficient = 40, maximum sample = 255, 40 terms
    // Maximum sum = 40 * 255 * (1+40)/2 = 40 * 255 * 20.5 = 209,100
    // Need at least 18 bits (2^18 = 262,144) to hold the sum.
    // Using 20 bits for safety.
    reg [19:0] sum;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear all delay line elements and output
            for (i = 0; i < 40; i = i + 1) begin
                delay_line[i] <= 8'd0;
            end
            y <= 16'd0;
        end else begin
            // Shift delay line and insert new sample
            // tap[0] = current x, tap[k] = previous tap[k-1]
            for (i = 39; i > 0; i = i - 1) begin
                delay_line[i] <= delay_line[i-1];
            end
            delay_line[0] <= x;

            // Compute sum of (k+1) * tap[k] for k=0..39
            sum = 20'd0;
            for (i = 0; i < 40; i = i + 1) begin
                sum = sum + ((i + 1) * delay_line[i]);
            end

            // Output the low 16 bits of the sum
            y <= sum[15:0];
        end
    end

endmodule