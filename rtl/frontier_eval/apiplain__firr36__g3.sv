module apiplain__firr36__g3 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // 36-element delay line (tap 0 = newest = current x)
    reg [7:0] taps [0:35];
    
    // Internal signals for accumulation
    integer k;
    reg [23:0] sum;  // Wide enough to hold sum (max value = 8'hFF * sum(1..36) = 255 * 666 = 169830, fits in 18 bits, use 24 for safety)
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear all taps and output
            for (k = 0; k < 36; k = k + 1) begin
                taps[k] <= 8'd0;
            end
            y <= 16'd0;
        end else begin
            // Shift delay line and insert new sample at tap 0
            for (k = 35; k > 0; k = k - 1) begin
                taps[k] <= taps[k-1];
            end
            taps[0] <= x;
            
            // Compute sum of (k+1) * tap[k] for k=0..35
            sum = 24'd0;
            for (k = 0; k < 36; k = k + 1) begin
                sum = sum + ((k + 1) * taps[k]);
            end
            
            // Output low 16 bits of the sum
            y <= sum[15:0];
        end
    end

endmodule