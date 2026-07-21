module apiplain__firr18__g2 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // 18-element delay line (tap 0 = newest sample)
    reg [7:0] delay_line [0:17];
    integer k;
    
    // Accumulator for sum of products (needs enough bits to prevent overflow)
    reg [23:0] sum;  // 8-bit * 5-bit coefficient => 13 bits per product, 
                      // 18 products => max 17 bits, plus safety margin
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear all delay line elements
            for (k = 0; k < 18; k = k + 1) begin
                delay_line[k] <= 8'd0;
            end
            y <= 16'd0;
        end else begin
            // Shift delay line and insert new sample at tap 0
            delay_line[0] <= x;
            for (k = 17; k > 0; k = k - 1) begin
                delay_line[k] <= delay_line[k-1];
            end
            
            // Compute sum of (k+1) * tap[k] for k = 0..17
            sum = 24'd0;
            for (k = 0; k < 18; k = k + 1) begin
                sum = sum + (delay_line[k] * (k + 1));
            end
            
            // Output low 16 bits of the sum
            y <= sum[15:0];
        end
    end

endmodule